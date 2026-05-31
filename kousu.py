import math
import os
import tkinter as tk
from datetime import datetime
from tkinter import messagebox

from config_manager import ConfigManager
from csv_processor import CsvProcessor


class KousuApp:
    """
    工数カウントくんのメインアプリケーションクラス（GUI・ロジック制御）。
    """

    def __init__(self, root):
        self.root = root

        # 設定マネージャーとCSVプロセッサーの初期化
        self.config = ConfigManager()
        folder_name = self.config.get("folder_name", "csvs")
        self.csv_processor = CsvProcessor(folder_name=folder_name)

        # 各種設定の読み込み
        self.standby_width = self.config.get("window_standby_width", 400)
        self.standby_height = self.config.get("window_standby_height", 250)
        self.counting_width = self.config.get("window_counting_width", 160)
        self.counting_height = self.config.get("window_counting_height", 100)

        self.font_family = self.config.get("system_font_family", "Arial")
        self.time_font_size = self.config.get("system_time_font_size", 30)
        self.normal_font_size = self.config.get("system_normal_font_size", 8)

        # 切り上げ単位（分）。例：15分、30分、等
        self.round_unit_minutes = self.config.get("round_unit_minutes", 15)

        # ウィンドウ初期設定
        self.root.title("工数カウントくん")
        self.root.geometry(f"{self.standby_width}x{self.standby_height}")
        self.root._offsetx = 0
        self.root._offsety = 0
        self.root.attributes("-topmost", True)

        # アプリケーション状態変数
        self.is_colon_displayed = True
        self.time_count_started = datetime.now()
        self.is_counting = False
        self.task_name = ""
        self.task_name_history = ["-"] * 5
        self.task_name_history_top = 0
        self.date_str = self.time_count_started.strftime("%Y%m%d")

        # 起動時のCSVファイル存在チェック（および読み込み）
        self.kousu_list = self.csv_processor.ensure_csv_file(self.date_str)
        # UIコンポーネントの構築
        self.create_widgets()

    def create_widgets(self):
        """GUIの配置を定義します。"""
        # 集計UIを追加するため、待機画面の高さを少し広げる調整（250 -> 320）
        self.standby_height = max(self.standby_height, 320)
        self.root.geometry(f"{self.standby_width}x{self.standby_height}")

        # --- 待機状態フレーム ---
        self.frame_standby = tk.Frame(
            self.root, width=self.standby_width, height=self.standby_height
        )

        self.btn_exit = tk.Button(self.frame_standby, text="exit", command=self.on_exit)
        self.btn_exit.place(x=0, y=0)

        self.entry_task_name = tk.Entry(self.frame_standby, width=35)
        self.entry_task_name.place(x=10, y=40)

        self.label_task_history = [0] * 5
        self.btn_task_history = [0] * 5
        for i in range(5):
            self.label_task_history[i] = tk.Label(self.frame_standby, text="-")
            self.label_task_history[i].place(x=10, y=120 + 20 * i)
            self.btn_task_history[i] = tk.Button(
                self.frame_standby,
                text="開始",
                command=self.start_counting_from_history(i),
            )
            self.btn_task_history[i].place(x=200, y=120 + 20 * i)

        self.btn_start = tk.Button(
            self.frame_standby,
            text="開始",
            command=lambda: self.start_counting(self.entry_task_name.get()),
        )
        self.btn_start.place(x=160, y=70)

        # ----------------------------------------------------
        # 追加：集計UIセクション
        # ----------------------------------------------------
        # 区切り線代わりのラベル
        lbl_border = tk.Label(
            self.frame_standby,
            text="------------------- 期間集計 -------------------",
            fg="gray",
        )
        lbl_border.place(x=10, y=230)

        # 開始日入力
        lbl_start = tk.Label(self.frame_standby, text="開始日 (YYYYMMDD):")
        lbl_start.place(x=10, y=255)
        self.entry_start_date = tk.Entry(self.frame_standby, width=10)
        self.entry_start_date.insert(0, self.date_str)  # 初期値として今日の日付
        self.entry_start_date.place(x=130, y=255)

        # 終了日入力
        lbl_end = tk.Label(self.frame_standby, text="終了日 (YYYYMMDD):")
        lbl_end.place(x=10, y=285)
        self.entry_end_date = tk.Entry(self.frame_standby, width=10)
        self.entry_end_date.insert(0, self.date_str)  # 初期値として今日の日付
        self.entry_end_date.place(x=130, y=285)

        # 集計実行ボタン
        self.btn_summary = tk.Button(
            self.frame_standby,
            text="集計を表示",
            command=self.show_summary,
        )
        self.btn_summary.place(x=230, y=265)
        # ----------------------------------------------------

        # --- カウント中フレーム ---
        self.frame_counting = tk.Frame(
            self.root, width=self.counting_width, height=self.counting_height
        )

        self.label_time = tk.Label(
            self.frame_counting,
            text="00:00:00",
            font=f"{self.font_family} {self.time_font_size}",
            anchor="n",
        )
        self.label_time.place(x=0, y=30)

        self.label_task_name = tk.Label(
            self.frame_counting,
            text="",
            font=f"{self.font_family} {self.normal_font_size}",
        )
        self.label_task_name.place(x=10, y=5)
        self.btn_stop = tk.Button(
            self.frame_counting, text="停止", command=self.stop_counting
        )
        self.btn_stop.place(x=115, y=75)

        # カウント状態のフレームにドラッグ移動イベントをバインド
        self.frame_counting.bind("<Button-1>", self.click_win)
        self.frame_counting.bind("<B1-Motion>", self.drag_win)

        # 時間表示のラベル（サイズが大きく重なるため、ここにもドラッグをバインド）
        self.label_time.bind("<Button-1>", self.click_win_text)
        self.label_time.bind("<B1-Motion>", self.drag_win)

        # 配置の決定と初期状態（待機フレーム）の最前面表示
        self.frame_counting.place(x=0, y=0)
        self.frame_standby.place(x=0, y=0)
        self.frame_standby.tkraise()

    def start_counting(self, task_name_arg):
        """計測を開始します。"""
        # 入力がない場合はデフォルト名を付与
        if not task_name_arg or task_name_arg.strip() == "":
            task_name_arg = "無題のタスク"

        self.root.geometry(f"{self.counting_width}x{self.counting_height}")
        self.frame_counting.tkraise()

        self.time_count_started = datetime.now()
        self.label_time["text"] = "00:00:00"
        self.is_counting = True
        self.task_name = task_name_arg
        self.label_task_name["text"] = self.task_name

        # 履歴への保存
        self.task_name_history[self.task_name_history_top] = self.task_name
        self.task_name_history_top = (self.task_name_history_top + 1) % 5

        # 500ms後にタイマー更新処理を起動
        self.root.after(500, self.refresh_counter)

    def start_counting_from_history(self, index):
        """履歴ボタンクリック時にその履歴名で計測を開始するための関数を生成します。"""
        return lambda: self.start_counting(self.label_task_history[index]["text"])

    def refresh_counter(self):
        """カウント画面の経過時間表示を更新します（コロン点滅アニメーションを含む）。"""
        if not self.is_counting:
            return

        time_diff = datetime.now() - self.time_count_started
        hour, amari = divmod(time_diff.seconds, 3600)
        minute, sec = divmod(amari, 60)

        # コロンの点滅（ぴこぴこ）処理
        if self.is_colon_displayed:
            self.label_time["text"] = (
                f"{str(hour).zfill(2)} {str(minute).zfill(2)} {str(sec).zfill(2)}"
            )
            self.is_colon_displayed = False
        else:
            self.label_time["text"] = (
                f"{str(hour).zfill(2)}:{str(minute).zfill(2)}:{str(sec).zfill(2)}"
            )
            self.is_colon_displayed = True

        if self.is_counting:
            self.root.after(500, self.refresh_counter)

    def refresh_task_histories(self):
        """待機画面の履歴ラベルを更新します。"""
        idx = self.task_name_history_top
        for i in range(5):
            idx = 4 if (idx == 0) else (idx - 1)
            self.label_task_history[i]["text"] = self.task_name_history[idx]

    def calculate_rounded_hours(self, total_seconds):
        """秒数を時間（h）に変換し、設定された切り上げ単位に丸めます。"""
        if self.round_unit_minutes <= 0:
            return total_seconds / 3600.0

        minutes = total_seconds / 60.0
        # math.ceilを用いて設定分数単位で切り上げ（例：15分単位）
        rounded_minutes = (
            math.ceil(minutes / self.round_unit_minutes) * self.round_unit_minutes
        )
        return rounded_minutes / 60.0

    def stop_counting(self):
        """計測を停止し、経過時間をCSVへ保存します。"""
        self.is_counting = False

        self.root.geometry(f"{self.standby_width}x{self.standby_height}")
        self.frame_standby.tkraise()
        self.refresh_task_histories()

        time_count_end = datetime.now()
        time_diff = time_count_end - self.time_count_started

        # 表示用の時間計算
        hour, amari = divmod(time_diff.seconds, 3600)
        minute, sec = divmod(amari, 60)

        # 切り上げ単位に基く記録用の時間計算
        rounded_hours = self.calculate_rounded_hours(time_diff.total_seconds())

        # メッセージの作成
        msg = f"作業:{self.task_name}\n稼働時間は {hour}時間{minute}分{sec}秒 です"
        if self.round_unit_minutes > 0:
            msg += (
                f"\n({self.round_unit_minutes}分単位切り上げ: {rounded_hours:.2f} 時間)"
            )

        messagebox.showinfo("stop", msg)

        # CSVへの書き込み
        try:
            self.csv_processor.write_record(
                date_str=self.date_str,
                task_name=self.task_name,
                duration=rounded_hours,
                start_time=self.time_count_started.strftime("%H:%M"),
                end_time=time_count_end.strftime("%H:%M"),
            )
        except PermissionError:
            messagebox.showinfo(
                "error",
                f"ファイル書き込みに失敗しました。（他のアプリでcsvファイルを開いていませんか？）\n"
                f"tmp/{self.date_str}_tmp.csv に今の記録を書き出したので、手動でマージしてください。",
            )

    def show_summary(self):
        """指定された期間のタスク工数を集計してポップアップ表示します。"""
        start_str = self.entry_start_date.get().strip()
        end_str = self.entry_end_date.get().strip()

        # 入力フォーマットのバリデーション
        try:
            datetime.strptime(start_str, "%Y%m%d")
            datetime.strptime(end_str, "%Y%m%d")
        except ValueError:
            messagebox.showerror(
                "エラー", "日付はYYYYMMDD形式（例: 20260531）で入力してください。"
            )
            return

        # CsvProcessorのメソッドを利用して集計ロジックを走らせる
        # get_summarized() は内部で print するだけで返り値を持たないため、
        # 同様の集計ロジックをここで安全に回す、または get_day_summarized を利用します。
        task_sum = {}
        try:
            start_date = datetime.strptime(start_str, "%Y%m%d")
            end_date = datetime.strptime(end_str, "%Y%m%d")
            current_date = start_date

            while current_date <= end_date:
                day_sum = self.csv_processor.get_day_summarized(current_date)
                for taskname, tasktime in day_sum.items():
                    task_sum[taskname] = task_sum.get(taskname, 0.0) + tasktime
                current_date += math.trunc(1) * (
                    datetime(2026, 5, 2) - datetime(2026, 5, 1)
                )  # 1日進める
        except Exception as e:
            messagebox.showerror("エラー", f"集計中にエラーが発生しました:\n{e}")
            return

        # 結果のテキスト整形
        if not task_sum:
            msg = f"{start_str} ～ {end_str}\n該当期間のデータ（CSV）が見つかりませんでした。"
            messagebox.showinfo("集計結果", msg)
            return

        msg = f"【集計期間】 {start_str} ～ {end_str}\n\n"
        msg += "タスク名 : 合計時間(h)\n"
        msg += "---------------------------------------\n"

        total_all_tasks = 0.0
        for task_name, total_time in task_sum.items():
            msg += f"・{task_name} : {total_time:.2f} 時間\n"
            total_all_tasks += total_time

        msg += "---------------------------------------\n"
        msg += f"総稼働時間: {total_all_tasks:.2f} 時間"

        # ポップアップ表示
        messagebox.showinfo("工数集計結果", msg)

    def on_exit(self):
        """アプリケーションを終了します。"""
        self.root.destroy()

    def drag_win(self, event):
        """カウントウィンドウをドラッグ移動します。"""
        x = self.root.winfo_pointerx() - self.root._offsetx
        y = self.root.winfo_pointery() - self.root._offsety
        self.root.geometry(f"+{x}+{y}")

    def click_win(self, event):
        """ドラッグ開始位置を記録します。"""
        self.root._offsetx = event.x
        self.root._offsety = event.y + 25

    def click_win_text(self, event):
        """時間ラベルをクリックした際のドラッグ開始位置を記録します。"""
        self.root._offsetx = event.x
        self.root._offsety = event.y + 46


if __name__ == "__main__":
    root = tk.Tk()
    app = KousuApp(root)
    root.mainloop()
