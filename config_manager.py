import json
import os


class ConfigManager:
    """
    設定ファイル（config.json）の読み込み・保存・管理を専門に行うクラス。
    """

    DEFAULT_CONFIG = {
        "window_standby_width": 400,
        "window_standby_height": 350,
        "window_counting_width": 160,
        "window_counting_height": 100,
        "system_font_family": "Arial",
        "system_time_font_size": 30,
        "system_normal_font_size": 8,
        "round_unit_minutes": 5,  # 切り上げ/丸め単位 (分)。0の場合は丸め処理なし
        "folder_name": "csvs",
    }

    def __init__(self, file_path="config.json"):
        self.file_path = file_path
        self.config = self.load_config()

    def load_config(self):
        """
        設定ファイルから設定を読み込みます。
        設定ファイルが存在しない場合はデフォルト値で新規作成します。
        既存ファイルに足りない設定項目がある場合は自動補完します。
        """
        if os.path.isfile(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    config = json.load(f)

                # 新しい設定項目が追加された際、既存の古いconfigファイルにも補完する
                updated = False
                for key, val in self.DEFAULT_CONFIG.items():
                    if key not in config:
                        config[key] = val
                        updated = True

                if updated:
                    self.save_config(config)

                return config
            except Exception as e:
                print(f"Error loading config file. Using default config. Error: {e}")
                return self.DEFAULT_CONFIG.copy()
        else:
            # 新規作成
            self.save_config(self.DEFAULT_CONFIG)
            return self.DEFAULT_CONFIG.copy()

    def save_config(self, config_data=None):
        """
        現在の設定内容をJSONファイルに保存します。
        """
        if config_data is not None:
            self.config = config_data

        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config file: {e}")

    def get(self, key, default=None):
        """設定値を取得します。"""
        return self.config.get(
            key, default if default is not None else self.DEFAULT_CONFIG.get(key)
        )

    def set(self, key, value):
        """設定値を更新し、ファイルへ即座に保存します。"""
        self.config[key] = value
        self.save_config()
