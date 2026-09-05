'''
import calendar
import math
import os
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import messagebox, ttk

from config_manager import ConfigManager
from csv_processor import CsvProcessor


class CalendarDialog(tk.Toplevel):
    """
    追加ライブラリなしで動作する、tkinter標準機能だけで作ったカレンダーダイアログ
    """

    def __init__(self, parent, title="日付選択"):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # 現在の年月を取得
        self.now = datetime.now()
        self.current_year = self.now.year
        self.current_month = self.now.month
        self.selected_date = None

        # ウィジェット作成
        self.header_frame = tk.Frame(self)
        self.header_frame.pack(pady=5)

        self.btn_prev = tk.Button(self.header_frame, text="◀", command=self.prev_month)
        self.btn_prev.pack(side=tk.LEFT, padx=10)

        self.lbl_month = tk.Label(
            self.header_frame, text="", font=("Arial", 10, "bold")
        )
        self.lbl_month.pack(side=tk.LEFT, padx=10)

        self.btn_next = tk.Button(self.header_frame, text="▶", command=self.next_month)
        self.btn_next.pack(side=tk.LEFT, padx=10)

        self.days_frame = tk.Frame(self)
        self.days_frame.pack(padx=10, pady=5)

        self.create_calendar()

    def create_calendar(self):
        # 古いカレンダーをクリア
        for widget in self.days_frame.winfo_children():
            widget.destroy()

        self.lbl_month.config(text=f"{self.current_year}年 {self.current_month}月")

        # 曜日ヘッダー
        weeks = ["日", "月", "火", "水", "木", "金", "土"]
        for col, week in enumerate(weeks):
            lbl = tk.Label(self.days_frame, text=week, width=4)
            lbl.grid(row=0, column=col)

        # カレンダーの日付を取得 (日曜日始まりに調整)
        cal = calendar.Calendar(firstweekday=6)
        month_days = cal.monthdayscalendar(self.current_year, self.current_month)

        for row, week in enumerate(month_days, start=1):
            for col, day in enumerate(week):
                if day == 0:
                    continue

                # ボタンとして配置
                btn = tk.Button(
                    self.days_frame,
                    text=str(day),
                    width=3,
                    command=lambda d=day: self.select_day(d),
                )
                btn.grid(row=row, column=col, padx=2, pady=2)

    def prev_month(self):
        self.current_month -= 1
        if self.current_month == 0:
            self.current_month = 12
            self.current_year -= 1
        self.create_calendar()

    def next_month(self):
        self.current_month += 1
        if self.current_month == 13:
            self.current_month = 1
            self.current_year += 1
        self.create_calendar()

    def select_day(self, day):
        # 選択された日付を YYYYMMDD 形式で保持
        self.selected_date = f"{self.current_year}{self.current_month:02d}{day:02d}"
        self.destroy()


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
        self.standby_height = self.config.get(
            "window_standby_height", 350
        )  # 高さを少し拡張
        self.counting_width = self.config.get("window_counting_width", 160)
        self.counting_height = self.config.get("window_counting_height", 100)

        self.font_family = self.config.get("system_font_family", "Arial")
        self.time_font_size = self.config.get("system_time_font_size", 30)
        self.normal_font_size = self.config.get("system_normal_font_size", 8)

        # 時間丸め設定
        self.round_unit_minutes = self.config.get("round_unit_minutes", 15)

        # ウィンドウの基本設定（枠なし、最前面）
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)

        # 状態管理変数
        self.is_counting = False
        self.task_name = ""
        self.time_count_started = None
        self.elapsed_seconds = 0

        # 今日の日付文字列
        self.date_str = datetime.now().strftime("%Y%m%d")

        # ウィジェットの生成と配置
        self.create_widgets()

        # 【修正後】 create_widgets メソッド内で、各フレームに対して個別にバインドする
        # 待機フレーム
        self.frame_standby.bind("<Button-1>", self.click_win)
        self.frame_standby.bind("<B1-Motion>", self.drag_win)

        # カウント中フレーム
        self.frame_counting.bind("<Button-1>", self.click_win)
        self.frame_counting.bind("<B1-Motion>", self.drag_win)

        # 集計画面フレーム
        self.frame_summary.bind("<Button-1>", self.click_win)
        self.frame_summary.bind("<B1-Motion>", self.drag_win)

        # 初期状態は待機画面を表示
        self.show_standby_frame()

    def create_widgets(self):
        """GUIの配置を定義します。"""
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

        # --- 期間集計UI（待機画面の下部） ---
        lbl_border = tk.Label(
            self.frame_standby,
            text="------------------- 期間集計 -------------------",
            fg="gray",
        )
        lbl_border.place(x=10, y=235)

        lbl_start = tk.Label(self.frame_standby, text="開始日:")
        lbl_start.place(x=10, y=260)
        self.entry_start_date = tk.Entry(self.frame_standby, width=10)
        self.entry_start_date.insert(0, self.date_str)
        self.entry_start_date.place(x=60, y=260)
        self.btn_cal_start = tk.Button(
            self.frame_standby,
            text="📅",
            command=lambda: self.pick_date(self.entry_start_date),
        )
        self.btn_cal_start.place(x=145, y=256)

        lbl_end = tk.Label(self.frame_standby, text="終了日:")
        lbl_end.place(x=10, y=295)
        self.entry_end_date = tk.Entry(self.frame_standby, width=10)
        self.entry_end_date.insert(0, self.date_str)
        self.entry_end_date.place(x=60, y=295)
        self.btn_cal_end = tk.Button(
            self.frame_standby,
            text="📅",
            command=lambda: self.pick_date(self.entry_end_date),
        )
        self.btn_cal_end.place(x=145, y=256 + 35)

        self.btn_summary = tk.Button(
            self.frame_standby,
            text="集計結果を表示",
            command=self.calc_and_show_summary,
        )
        self.btn_summary.place(x=200, y=275)

        # --- カウント中フレーム ---
        self.frame_counting = tk.Frame(
            self.root, width=self.counting_width, height=self.counting_height
        )
        self.label_task_name_display = tk.Label(
            self.frame_counting,
            text="task_name",
            font=(self.font_family, self.normal_font_size),
        )
        self.label_task_name_display.place(x=5, y=5)

        self.label_time = tk.Label(
            self.frame_counting,
            text="00:00",
            font=(self.font_family, self.time_font_size),
        )
        self.label_time.place(x=20, y=20)

        self.btn_stop = tk.Button(
            self.frame_counting, text="stop", command=self.stop_counting
        )
        self.btn_stop.place(x=60, y=70)

        # --- 新設：集計結果画面フレーム ---
        self.frame_summary = tk.Frame(
            self.root, width=self.standby_width, height=self.standby_height
        )
        self.lbl_summary_title = tk.Label(
            self.frame_summary,
            text="【工数集計結果】",
            font=(self.font_family, 10, "bold"),
        )
        self.lbl_summary_title.pack(pady=5)

        # ★変更: 表形式（Treeview）の作成
        # columnsで列の名前を定義、show="headings"で1列目の不要なツリー用矢印スペースを非表示にします
        self.tree_summary = ttk.Treeview(
            self.frame_summary, columns=("task", "time"), show="headings", height=10
        )

        # 列のヘッダー名と幅・アライメントの設定
        self.tree_summary.heading("task", text="タスク名")
        self.tree_summary.heading("time", text="合計時間 (h)")

        self.tree_summary.column("task", width=240, anchor=tk.W)  # 左寄せ
        self.tree_summary.column("time", width=100, anchor=tk.E)  # 右寄せ
        self.tree_summary.pack(padx=10, pady=5)

        # 総計時間を表示するための下部ラベル
        self.lbl_total_all = tk.Label(
            self.frame_summary,
            text="総計稼働時間: 0.00 時間",
            font=(self.font_family, 9, "bold"),
        )
        self.lbl_total_all.pack(pady=2)

        self.btn_back_to_standby = tk.Button(
            self.frame_summary, text="戻る", command=self.show_standby_frame
        )
        self.btn_back_to_standby.pack(pady=5)

    def pick_date(self, target_entry):
        """カレンダーダイアログを開き、選択された日付をEntryにセットします。"""
        dialog = CalendarDialog(self.root)
        self.root.wait_window(dialog)
        if dialog.selected_date:
            target_entry.delete(0, tk.END)
            target_entry.insert(0, dialog.selected_date)

    def calc_and_show_summary(self):
        """期間内のCSVからデータを集計し、専用フレームに表示します。"""
        start_str = self.entry_start_date.get().strip()
        end_str = self.entry_end_date.get().strip()

        try:
            start_date = datetime.strptime(start_str, "%Y%m%d")
            end_date = datetime.strptime(end_str, "%Y%m%d")
        except ValueError:
            messagebox.showerror("エラー", "日付はYYYYMMDD形式で指定してください。")
            return

        # 期間ループを回して集計
        task_sum = {}
        current_date = start_date
        while current_date <= end_date:
            day_sum = self.csv_processor.get_day_summarized(current_date)
            for taskname, tasktime in day_sum.items():
                task_sum[taskname] = task_sum.get(taskname, 0.0) + tasktime
            current_date += timedelta(days=1)

        # 集計結果フレームの表示に切り替え
        self.frame_standby.pack_forget()
        self.frame_counting.pack_forget()
        self.frame_summary.pack()
        self.root.geometry(f"{self.standby_width}x{self.standby_height}")

        # 表の既存データを一旦すべて削除
        for item in self.tree_summary.get_children():
            self.tree_summary.delete(item)

        # タイトルに期間を反映
        self.lbl_summary_title.config(text=f"【工数集計結果】 {start_str} ～ {end_str}")

        if not task_sum:
            self.tree_summary.insert("", tk.END, values=("（データなし）", "0.00"))
            self.lbl_total_all.config(text="総計稼働時間: 0.00 時間")
            return

        # データを表に挿入
        total_all = 0.0
        task_sum_sorted = dict(
            sorted(task_sum.items(), key=lambda x: x[1], reverse=True)
        )
        for name, time_val in task_sum_sorted.items():
            # valuesにタプルで渡すことで各列に綺麗に収まります
            self.tree_summary.insert("", tk.END, values=(name, f"{time_val:.2f}"))
            total_all += time_val

        # 総計ラベルの更新
        self.lbl_total_all.config(text=f"総計稼働時間: {total_all:.2f} 時間")

    def show_standby_frame(self):
        """待機画面フレームを表示します。履歴も自動更新します。"""
        self.frame_counting.pack_forget()
        self.frame_summary.pack_forget()
        self.frame_standby.pack()
        self.root.geometry(f"{self.standby_width}x{self.standby_height}")
        self.update_history_labels()

    def update_history_labels(self):
        """CSVから直近の履歴を読み込み、ラベルを更新します。"""
        filename = self.csv_processor.get_csv_path(self.date_str)
        res_list = self.csv_processor.try_read_rows_from_csv(filename)
        if res_list["result"]:
            rows = res_list["list"][1:]  # ヘッダーを除く
            recent_rows = rows[-5:]  # 直近5件
            recent_rows.reverse()  # 新しい順

            for i in range(5):
                if i < len(recent_rows):
                    task_name = recent_rows[i][0]
                    # 長すぎるタスク名は切り詰める
                    display_name = (
                        task_name if len(task_name) <= 15 else task_name[:14] + "…"
                    )
                    self.label_task_history[i].config(text=display_name)
                    self.btn_task_history[i].config(state=tk.NORMAL)
                else:
                    self.label_task_history[i].config(text="-")
                    self.btn_task_history[i].config(state=tk.DISABLED)
        else:
            for i in range(5):
                self.label_task_history[i].config(text="-")
                self.btn_task_history[i].config(state=tk.DISABLED)

    def start_counting_from_history(self, index):
        """履歴ボタンクリック時のコールバック関数を生成します。"""
        return lambda: self.start_counting(self.label_task_history[index].cget("text"))

    def start_counting(self, task_name):
        """タイマーカウントを開始します。"""
        if not task_name or task_name == "-" or task_name.endswith("…"):
            # 簡略化のため空文字等の場合は入力を促すか、デフォルト値を設定
            task_name = self.entry_task_name.get().strip()
            if not task_name:
                messagebox.showwarning("warning", "タスク名を入力してください。")
                return

        self.task_name = task_name
        self.is_counting = True
        self.time_count_started = datetime.now()
        self.elapsed_seconds = 0

        # 画面表示の切り替え
        self.frame_standby.pack_forget()
        self.frame_summary.pack_forget()
        self.frame_counting.pack()
        self.root.geometry(f"{self.counting_width}x{self.counting_height}")

        self.label_task_name_display.config(text=self.task_name)
        self.update_timer()

    def update_timer(self):
        """タイマーのカウントアップ処理（1秒周期）。"""
        if self.is_counting:
            self.elapsed_seconds += 1
            minutes = self.elapsed_seconds // 60
            seconds = self.elapsed_seconds % 60
            self.label_time.config(text=f"{minutes:02d}:{seconds:02d}")
            self.root.after(1000, self.update_timer)

    def stop_counting(self):
        """タイマーを停止し、結果をCSVへ記録します。"""
        self.is_counting = False
        time_count_end = datetime.now()

        # 時間計算（時間単位）
        actual_hours = self.elapsed_seconds / 3600.0

        # 指定分数単位での切り上げ計算
        minutes_elapsed = self.elapsed_seconds / 60.0
        rounded_minutes = (
            math.ceil(minutes_elapsed / self.round_unit_minutes)
            * self.round_unit_minutes
        )
        rounded_hours = rounded_minutes / 60.0

        msg = (
            f"タスク: {self.task_name}\n"
            f"経過時間: {minutes_elapsed:.1f} 分\n"
            f"実時間: {actual_hours:.2f} 時間"
        )
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

        # 待機画面へ戻る
        self.show_standby_frame()

    def on_exit(self):
        """アプリケーションを終了します。"""
        self.root.destroy()

    def drag_win(self, event):
        """カウントウィンドウをドラッグ移動します。"""
        x = self.root.winfo_pointerx() - self.root._offsetx
        y = self.root.winfo_pointery() - self.root._offsety
        self.root.geometry(f"+{x}+{y}")

    def click_win(self, event):
        """ドラッグ開始時のマウス位置を記録します。"""
        self.root._offsetx = event.x
        self.root._offsety = event.y


if __name__ == "__main__":
    root = tk.Tk()
    app = KousuApp(root)
    root.mainloop()
'''
import calendar
import math
import os
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import messagebox, simpledialog, ttk

from config_manager import ConfigManager
from csv_processor import CsvProcessor

IDLE_NOTICE_SECONDS = 15 * 60


def seconds_between(start, end):
    """開始・終了時刻から経過秒数を求める（スリープ復帰後も正しい）。"""
    return max(0.0, (end - start).total_seconds())


def rounded_hours(start, end, unit_minutes=0):
    seconds = seconds_between(start, end)
    if unit_minutes and unit_minutes > 0:
        seconds = math.ceil(seconds / (unit_minutes * 60)) * unit_minutes * 60
    return seconds / 3600.0


def parse_time_today(value, now=None):
    """HH:MM を今日の日付の datetime に変換する。"""
    current = now or datetime.now()
    parsed = datetime.strptime(value.strip(), "%H:%M")
    return current.replace(
        hour=parsed.hour, minute=parsed.minute, second=0, microsecond=0
    )


class CalendarDialog(tk.Toplevel):
    """
    追加ライブラリなしで動作する、tkinter標準機能だけで作ったカレンダーダイアログ
    """

    def __init__(self, parent, title="日付選択"):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # 現在の年月を取得
        self.now = datetime.now()
        self.current_year = self.now.year
        self.current_month = self.now.month
        self.selected_date = None

        # ウィジェット作成
        self.header_frame = tk.Frame(self)
        self.header_frame.pack(pady=5)

        self.btn_prev = tk.Button(self.header_frame, text="◀", command=self.prev_month)
        self.btn_prev.pack(side=tk.LEFT, padx=10)

        self.lbl_month = tk.Label(
            self.header_frame, text="", font=("Arial", 10, "bold")
        )
        self.lbl_month.pack(side=tk.LEFT, padx=10)

        self.btn_next = tk.Button(self.header_frame, text="▶", command=self.next_month)
        self.btn_next.pack(side=tk.LEFT, padx=10)

        self.days_frame = tk.Frame(self)
        self.days_frame.pack(padx=10, pady=5)

        self.create_calendar()

    def create_calendar(self):
        # 古いカレンダーをクリア
        for widget in self.days_frame.winfo_children():
            widget.destroy()

        self.lbl_month.config(text=f"{self.current_year}年 {self.current_month}月")

        # 曜日ヘッダー
        weeks = ["日", "月", "火", "水", "木", "金", "土"]
        for col, week in enumerate(weeks):
            lbl = tk.Label(self.days_frame, text=week, width=4)
            lbl.grid(row=0, column=col)

        # カレンダーの日付を取得 (日曜日始まりに調整)
        cal = calendar.Calendar(firstweekday=6)
        month_days = cal.monthdayscalendar(self.current_year, self.current_month)

        for row, week in enumerate(month_days, start=1):
            for col, day in enumerate(week):
                if day == 0:
                    continue

                # ボタンとして配置
                btn = tk.Button(
                    self.days_frame,
                    text=str(day),
                    width=3,
                    command=lambda d=day: self.select_day(d),
                )
                btn.grid(row=row, column=col, padx=2, pady=2)

    def prev_month(self):
        self.current_month -= 1
        if self.current_month == 0:
            self.current_month = 12
            self.current_year -= 1
        self.create_calendar()

    def next_month(self):
        self.current_month += 1
        if self.current_month == 13:
            self.current_month = 1
            self.current_year += 1
        self.create_calendar()

    def select_day(self, day):
        # 選択された日付を YYYYMMDD 形式で保持
        self.selected_date = f"{self.current_year}{self.current_month:02d}{day:02d}"
        self.destroy()


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
        self.standby_height = self.config.get(
            "window_standby_height", 350
        )  # 高さを少し拡張
        self.counting_width = self.config.get("window_counting_width", 160)
        self.counting_height = max(130, self.config.get("window_counting_height", 130))

        self.font_family = self.config.get("system_font_family", "Arial")
        self.time_font_size = self.config.get("system_time_font_size", 30)
        self.normal_font_size = self.config.get("system_normal_font_size", 8)

        # 時間丸め設定
        self.round_unit_minutes = self.config.get("round_unit_minutes", 15)

        # 通常のウィンドウとして表示し、Windowsのタスクバーに登録する。
        # 最前面表示も維持して、背面に隠れた場合でも見失いにくくする。
        self.root.title("工数カウントくん")
        self.root.overrideredirect(False)
        self.root.attributes("-topmost", True)

        # 状態管理変数
        self.is_counting = False
        self.task_name = ""
        self.time_count_started = None
        self.elapsed_seconds = 0
        self.idle_notice_sent = False
        self.idle_started_at = datetime.now()

        # 今日の日付文字列
        self.date_str = datetime.now().strftime("%Y%m%d")

        # ウィジェットの生成と配置
        self.create_widgets()

        # 【修正後】 create_widgets メソッド内で、各フレームに対して個別にバインドする
        # 待機フレーム
        self.frame_standby.bind("<Button-1>", self.click_win)
        self.frame_standby.bind("<B1-Motion>", self.drag_win)

        # カウント中フレーム
        self.frame_counting.bind("<Button-1>", self.click_win)
        self.frame_counting.bind("<B1-Motion>", self.drag_win)

        # 集計画面フレーム
        self.frame_summary.bind("<Button-1>", self.click_win)
        self.frame_summary.bind("<B1-Motion>", self.drag_win)

        # 初期状態は待機画面を表示
        self.show_standby_frame()
        self.root.after(1000, self.check_idle)

    def create_widgets(self):
        """GUIの配置を定義します。"""
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

        self.btn_start_at = tk.Button(self.frame_standby, text="開始時刻を指定", command=self.start_counting_with_time)
        self.btn_start_at.place(x=235, y=70)

        # --- 期間集計UI（待機画面の下部） ---
        lbl_border = tk.Label(
            self.frame_standby,
            text="------------------- 期間集計 -------------------",
            fg="gray",
        )
        lbl_border.place(x=10, y=235)

        lbl_start = tk.Label(self.frame_standby, text="開始日:")
        lbl_start.place(x=10, y=260)
        self.entry_start_date = tk.Entry(self.frame_standby, width=10)
        self.entry_start_date.insert(0, self.date_str)
        self.entry_start_date.place(x=60, y=260)
        self.btn_cal_start = tk.Button(
            self.frame_standby,
            text="📅",
            command=lambda: self.pick_date(self.entry_start_date),
        )
        self.btn_cal_start.place(x=145, y=256)

        lbl_end = tk.Label(self.frame_standby, text="終了日:")
        lbl_end.place(x=10, y=295)
        self.entry_end_date = tk.Entry(self.frame_standby, width=10)
        self.entry_end_date.insert(0, self.date_str)
        self.entry_end_date.place(x=60, y=295)
        self.btn_cal_end = tk.Button(
            self.frame_standby,
            text="📅",
            command=lambda: self.pick_date(self.entry_end_date),
        )
        self.btn_cal_end.place(x=145, y=256 + 35)

        self.btn_summary = tk.Button(
            self.frame_standby,
            text="集計結果を表示",
            command=self.calc_and_show_summary,
        )
        self.btn_summary.place(x=200, y=275)

        # --- カウント中フレーム ---
        self.frame_counting = tk.Frame(
            self.root, width=self.counting_width, height=self.counting_height
        )
        self.label_task_name_display = tk.Label(
            self.frame_counting,
            text="task_name",
            font=(self.font_family, self.normal_font_size),
        )
        self.label_task_name_display.place(x=5, y=5)

        self.label_time = tk.Label(
            self.frame_counting,
            text="00:00",
            font=(self.font_family, self.time_font_size),
        )
        self.label_time.place(x=20, y=20)

        self.btn_stop = tk.Button(
            self.frame_counting, text="stop", command=self.stop_counting
        )
        self.btn_stop.place(x=60, y=70)
        self.btn_interrupt = tk.Button(self.frame_counting, text="中断", command=self.interrupt_counting)
        self.btn_interrupt.place(x=5, y=70)
        self.btn_stop_at = tk.Button(self.frame_counting, text="終了時刻を指定", command=self.stop_counting_with_time)
        self.btn_stop_at.place(x=5, y=95)

        # --- 新設：集計結果画面フレーム ---
        self.frame_summary = tk.Frame(
            self.root, width=self.standby_width, height=self.standby_height
        )
        self.lbl_summary_title = tk.Label(
            self.frame_summary,
            text="【工数集計結果】",
            font=(self.font_family, 10, "bold"),
        )
        self.lbl_summary_title.pack(pady=5)

        # ★変更: 表形式（Treeview）の作成
        # columnsで列の名前を定義、show="headings"で1列目の不要なツリー用矢印スペースを非表示にします
        self.tree_summary = ttk.Treeview(
            self.frame_summary, columns=("task", "time"), show="headings", height=10
        )

        # 列のヘッダー名と幅・アライメントの設定
        self.tree_summary.heading("task", text="タスク名")
        self.tree_summary.heading("time", text="合計時間 (h)")

        self.tree_summary.column("task", width=240, anchor=tk.W)  # 左寄せ
        self.tree_summary.column("time", width=100, anchor=tk.E)  # 右寄せ
        self.tree_summary.pack(padx=10, pady=5)

        # 総計時間を表示するための下部ラベル
        self.lbl_total_all = tk.Label(
            self.frame_summary,
            text="総計稼働時間: 0.00 時間",
            font=(self.font_family, 9, "bold"),
        )
        self.lbl_total_all.pack(pady=2)

        self.btn_back_to_standby = tk.Button(
            self.frame_summary, text="戻る", command=self.show_standby_frame
        )
        self.btn_back_to_standby.pack(pady=5)

    def pick_date(self, target_entry):
        """カレンダーダイアログを開き、選択された日付をEntryにセットします。"""
        dialog = CalendarDialog(self.root)
        self.root.wait_window(dialog)
        if dialog.selected_date:
            target_entry.delete(0, tk.END)
            target_entry.insert(0, dialog.selected_date)

    def calc_and_show_summary(self):
        """期間内のCSVからデータを集計し、専用フレームに表示します。"""
        start_str = self.entry_start_date.get().strip()
        end_str = self.entry_end_date.get().strip()

        try:
            start_date = datetime.strptime(start_str, "%Y%m%d")
            end_date = datetime.strptime(end_str, "%Y%m%d")
        except ValueError:
            messagebox.showerror("エラー", "日付はYYYYMMDD形式で指定してください。")
            return

        # 期間ループを回して集計
        task_sum = {}
        current_date = start_date
        while current_date <= end_date:
            day_sum = self.csv_processor.get_day_summarized(current_date)
            for taskname, tasktime in day_sum.items():
                task_sum[taskname] = task_sum.get(taskname, 0.0) + tasktime
            current_date += timedelta(days=1)

        # 集計結果フレームの表示に切り替え
        self.frame_standby.pack_forget()
        self.frame_counting.pack_forget()
        self.frame_summary.pack()
        self.root.geometry(f"{self.standby_width}x{self.standby_height}")

        # 表の既存データを一旦すべて削除
        for item in self.tree_summary.get_children():
            self.tree_summary.delete(item)

        # タイトルに期間を反映
        self.lbl_summary_title.config(text=f"【工数集計結果】 {start_str} ～ {end_str}")

        if not task_sum:
            self.tree_summary.insert("", tk.END, values=("（データなし）", "0.00"))
            self.lbl_total_all.config(text="総計稼働時間: 0.00 時間")
            return

        # データを表に挿入
        total_all = 0.0
        task_sum_sorted = dict(
            sorted(task_sum.items(), key=lambda x: x[1], reverse=True)
        )
        for name, time_val in task_sum_sorted.items():
            # valuesにタプルで渡すことで各列に綺麗に収まります
            self.tree_summary.insert("", tk.END, values=(name, f"{time_val:.2f}"))
            total_all += time_val

        # 総計ラベルの更新
        self.lbl_total_all.config(text=f"総計稼働時間: {total_all:.2f} 時間")

    def show_standby_frame(self):
        """待機画面フレームを表示します。履歴も自動更新します。"""
        self.frame_counting.pack_forget()
        self.frame_summary.pack_forget()
        self.frame_standby.pack()
        self.root.geometry(f"{self.standby_width}x{self.standby_height}")
        self.idle_started_at = datetime.now()
        self.idle_notice_sent = False
        self.update_history_labels()

    def update_history_labels(self):
        """CSVから直近の履歴を読み込み、ラベルを更新します。"""
        filename = self.csv_processor.get_csv_path(self.date_str)
        res_list = self.csv_processor.try_read_rows_from_csv(filename)
        if res_list["result"]:
            rows = res_list["list"]
            if rows and rows[0] == self.csv_processor.header:
                rows = rows[1:]  # ヘッダーを除く
            recent_rows = rows[-5:]  # 直近5件
            recent_rows.reverse()  # 新しい順

            for i in range(5):
                if i < len(recent_rows):
                    task_name = recent_rows[i][0]
                    # 長すぎるタスク名は切り詰める
                    display_name = (
                        task_name if len(task_name) <= 15 else task_name[:14] + "…"
                    )
                    self.label_task_history[i].config(text=display_name)
                    # 表示用に省略しても、開始時には元のタスク名を使う。
                    self.btn_task_history[i].config(
                        state=tk.NORMAL,
                        command=lambda name=task_name: self.start_counting(name),
                    )
                else:
                    self.label_task_history[i].config(text="-")
                    self.btn_task_history[i].config(state=tk.DISABLED)
        else:
            for i in range(5):
                self.label_task_history[i].config(text="-")
                self.btn_task_history[i].config(state=tk.DISABLED)

    def start_counting_from_history(self, index):
        """履歴ボタンクリック時のコールバック関数を生成します。"""
        # ボタン押下時点のラベルを読む。履歴更新後の古いクロージャを参照しない。
        return lambda: self.start_counting(self.label_task_history[index].cget("text"))

    def start_counting_with_time(self):
        value = simpledialog.askstring("開始時刻", "記録上の開始時刻 (HH:MM):", parent=self.root)
        if value is None:
            return
        try:
            start = parse_time_today(value)
        except ValueError:
            messagebox.showerror("エラー", "HH:MM 形式で入力してください。")
            return
        self.start_counting(self.entry_task_name.get(), start)

    def start_counting(self, task_name, start_time=None):
        """タイマーカウントを開始します。"""
        if not task_name or task_name == "-":
            # 簡略化のため空文字等の場合は入力を促すか、デフォルト値を設定
            task_name = self.entry_task_name.get().strip()
            if not task_name:
                messagebox.showwarning("warning", "タスク名を入力してください。")
                return

        self.task_name = task_name
        self.is_counting = True
        self.time_count_started = start_time or datetime.now()
        self.elapsed_seconds = 0

        # 画面表示の切り替え
        self.frame_standby.pack_forget()
        self.frame_summary.pack_forget()
        self.frame_counting.pack()
        self.root.geometry(f"{self.counting_width}x{self.counting_height}")

        self.label_task_name_display.config(text=self.task_name)
        self.idle_notice_sent = True
        self.update_timer()

    def update_timer(self):
        """タイマーのカウントアップ処理（1秒周期）。"""
        if self.is_counting:
            self.elapsed_seconds = int(seconds_between(self.time_count_started, datetime.now()))
            minutes = self.elapsed_seconds // 60
            seconds = self.elapsed_seconds % 60
            self.label_time.config(text=f"{minutes:02d}:{seconds:02d}")
            self.root.after(1000, self.update_timer)

    def stop_counting(self, end_time=None):
        """タイマーを停止し、結果をCSVへ記録します。"""
        self.is_counting = False
        time_count_end = end_time or datetime.now()

        # 時間計算（時間単位）
        actual_hours = seconds_between(self.time_count_started, time_count_end) / 3600.0

        # 指定分数単位での切り上げ計算
        minutes_elapsed = seconds_between(self.time_count_started, time_count_end) / 60.0
        rounded_minutes = math.ceil(minutes_elapsed / self.round_unit_minutes) * self.round_unit_minutes if self.round_unit_minutes > 0 else minutes_elapsed
        rounded_hours = rounded_minutes / 60.0

        msg = (
            f"タスク: {self.task_name}\n"
            f"経過時間: {minutes_elapsed:.1f} 分\n"
            f"実時間: {actual_hours:.2f} 時間"
        )
        if self.round_unit_minutes > 0:
            msg += (
                f"\n({self.round_unit_minutes}分単位切り上げ: {rounded_hours:.2f} 時間)"
            )

        messagebox.showinfo("stop", msg)

        # CSVへの書き込み
        try:
            self.csv_processor.write_record(
                date_str=self.time_count_started.strftime("%Y%m%d"),
                task_name=self.task_name,
                duration=rounded_hours,
                start_time=self.time_count_started.strftime("%H:%M"),
                end_time=time_count_end.strftime("%H:%M"),
            )
        except PermissionError:
            messagebox.showinfo(
                "error",
                f"ファイル書き込みに失敗しました。（他のアプリでcsvファイルを開いていませんか？）\n"
                f"tmp/{self.time_count_started.strftime('%Y%m%d')}_tmp.csv に今の記録を書き出したので、手動でマージしてください。",
            )

        # 待機画面へ戻る
        self.show_standby_frame()

    def stop_counting_with_time(self):
        value = simpledialog.askstring("終了時刻", "記録上の終了時刻 (HH:MM):", parent=self.root)
        if value is None:
            return
        try:
            end = parse_time_today(value)
        except ValueError:
            messagebox.showerror("エラー", "HH:MM 形式で入力してください。")
            return
        if end < self.time_count_started:
            messagebox.showerror("エラー", "終了時刻は開始時刻以降にしてください。")
            return
        self.stop_counting(end)

    def interrupt_counting(self):
        """タイマーを止め、作業記録を保存しない。"""
        self.is_counting = False
        self.show_standby_frame()

    def check_idle(self):
        if not self.is_counting:
            idle_seconds = seconds_between(self.idle_started_at, datetime.now())
            if idle_seconds >= IDLE_NOTICE_SECONDS and not self.idle_notice_sent:
                self.idle_notice_sent = True
                self.root.bell()
                self.flash_taskbar()
        else:
            self.idle_started_at = datetime.now()
            self.idle_notice_sent = False
        self.root.after(1000, self.check_idle)

    def flash_taskbar(self):
        """Windowsのタスクバーアイコンを点滅させる。Windows以外では無視する。"""
        if os.name != "nt":
            return
        try:
            import ctypes
            class FlashInfo(ctypes.Structure):
                _fields_ = [("cbSize", ctypes.c_uint), ("hwnd", ctypes.c_void_p),
                            ("flags", ctypes.c_uint), ("count", ctypes.c_uint),
                            ("timeout", ctypes.c_uint)]
            info = FlashInfo(ctypes.sizeof(FlashInfo), self.root.winfo_id(), 3, 5, 0)
            ctypes.windll.user32.FlashWindowEx(ctypes.byref(info))
        except (AttributeError, OSError):
            pass

    def on_exit(self):
        """アプリケーションを終了します。"""
        self.root.destroy()

    def drag_win(self, event):
        """カウントウィンドウをドラッグ移動します。"""
        x = self.root.winfo_pointerx() - self.root._offsetx
        y = self.root.winfo_pointery() - self.root._offsety
        self.root.geometry(f"+{x}+{y}")

    def click_win(self, event):
        """ドラッグ開始時のマウス位置を記録します。"""
        self.root._offsetx = event.x
        self.root._offsety = event.y


if __name__ == "__main__":
    root = tk.Tk()
    app = KousuApp(root)
    root.mainloop()
