import csv
import os
from datetime import datetime


class CsvProcessor:
    """
    作業工数データのCSV保存・読み込みを専門に行うクラス。
    """

    def __init__(self, folder_name="csvs"):
        self.folder_name = folder_name
        self.tmp_folder_name = os.path.join(folder_name, "tmp")

        # 保存先フォルダおよび一時退避フォルダの自動生成（安全対策）
        os.makedirs(self.folder_name, exist_ok=True)
        os.makedirs(self.tmp_folder_name, exist_ok=True)

        self.header = ["タスク名", "作業時間", "開始時刻", "終了時刻"]

    def get_csv_path(self, date_str):
        """日付ごとのCSVファイルパスを取得します。"""
        return os.path.join(self.folder_name, f"{date_str}.csv")

    def get_tmp_csv_path(self, date_str):
        """一時保存用（PermissionError時）のCSVファイルパスを取得します。"""
        return os.path.join(self.tmp_folder_name, f"{date_str}_tmp.csv")

    def ensure_csv_file(self, date_str):
        """
        指定された日付のCSVファイルの存在確認を行います。
        存在する場合はその内容をリストとして読み込み、存在しない場合はヘッダー付きで新規作成します。
        Excel等で開けるよう、文字コードは 'utf-8-sig'（BOM付き）を使用します。

        Returns:
            list: CSVの内容（行ごとのリスト）
        """
        csv_path = self.get_csv_path(date_str)

        if os.path.isfile(csv_path):
            try:
                # BOM付きUTF-8で読み込み
                with open(csv_path, mode="r", encoding="utf-8-sig", newline="") as f:
                    csv_reader = csv.reader(f)
                    return list(csv_reader)
            except Exception:
                # フォールバック
                with open(csv_path, mode="r", encoding="utf-8", newline="") as f:
                    csv_reader = csv.reader(f)
                    return list(csv_reader)
        else:
            # 新規作成
            with open(csv_path, mode="w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(self.header)
            return []

    def write_record(self, date_str, task_name, duration, start_time, end_time):
        """
        作業記録をCSVファイルに追記します。
        ファイルが開かれているなどで書き込みエラー（PermissionError）が発生した場合は、
        tmpフォルダ内のファイルに一時退避させて、PermissionErrorを再送出します。

        Args:
            date_str (str): 日付文字列 (YYYYMMDD)
            task_name (str): タスク名
            duration (float): 作業時間（時間単位、例: 1.5）
            start_time (str): 開始時刻 ("HH:MM")
            end_time (str): 終了時刻 ("HH:MM")
        """
        csv_path = self.get_csv_path(date_str)
        data = [[task_name, duration, start_time, end_time]]

        try:
            # Excelでの日本語文字化け防止のためutf-8-sigを使用
            with open(csv_path, mode="a", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)
                writer.writerows(data)
            return True
        except PermissionError as e:
            # メインCSVが他アプリで開かれている場合は、tmpフォルダに保存
            tmp_path = self.get_tmp_csv_path(date_str)

            # tmpファイルが未作成の場合は、ヘッダーも作成する（より親切な実装に改善）
            is_new_tmp = not os.path.isfile(tmp_path)

            with open(tmp_path, mode="a", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)
                if is_new_tmp:
                    writer.writerow(self.header)
                writer.writerows(data)

            # 例外を再送出してUI（kousu.py）側にポップアップ表示等のハンドリングを任せる
            raise e
