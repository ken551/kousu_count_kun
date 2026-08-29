import csv
import os
from datetime import datetime, timedelta


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

    def try_read_rows_from_csv(self, filename):
        retList = []
        result = True
        if os.path.isfile(filename):
            try:
                # BOM付きUTF-8で読み込み
                with open(filename, mode="r", encoding="utf-8-sig", newline="") as f:
                    csv_reader = csv.reader(f)
                    retList = list(csv_reader)
                    result = True
            except Exception:
                # フォールバック
                with open(filename, mode="r", encoding="utf-8", newline="") as f:
                    csv_reader = csv.reader(f)
                    retList = list(csv_reader)
                    result = True
        else:
            result = False
        return {"result": result, "list": retList}

    def ensure_csv_file(self, date_str):
        """
        指定された日付のCSVファイルの存在確認を行います。
        存在する場合はその内容をリストとして読み込み、存在しない場合はヘッダー付きで新規作成します。
        Excel等で開けるよう、文字コードは 'utf-8-sig'（BOM付き）を使用します。

        Returns:
            list: CSVの内容（行ごとのリスト）
        """
        csv_path = self.get_csv_path(date_str)

        lists = self.try_read_rows_from_csv(csv_path)

        rows = lists["list"] if lists["result"] else []
        # 旧版はヘッダーなしで出力していたため、既存ファイルも正規化する。
        if not rows or rows[0] != self.header:
            data_rows = rows if not (rows and rows[0] == self.header) else rows[1:]
            with open(csv_path, mode="w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(self.header)
                writer.writerows(data_rows)
            return [self.header] + data_rows
        return rows

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
        self.ensure_csv_file(date_str)
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

    def get_day_summarized(self, current_date):
        task_sum = {}

        current_date_str = current_date.strftime("%Y%m%d")
        filename = self.get_csv_path(current_date_str)
        res_list = self.try_read_rows_from_csv(filename)
        if res_list["result"]:
            rows = res_list["list"]
            if rows and rows[0] == self.header:
                rows = rows[1:]
            for row in rows:
                if len(row) < 2:
                    continue
                task_name = row[0]
                worktime_sum = task_sum.get(task_name, 0.0)
                worktime_sum = worktime_sum + float(row[1])
                task_sum[task_name] = worktime_sum
        else:
            pass
            # do nothing

        return task_sum

    def get_summarized(self, start_date_str, end_date_str):
        task_sum = {}

        start_date = datetime.strptime(start_date_str, "%Y%m%d")
        end_date = datetime.strptime(end_date_str, "%Y%m%d")
        current_date = start_date

        while current_date <= end_date:
            day_sum = self.get_day_summarized(current_date)
            for taskname, tasktime in day_sum.items():
                tmp_sum_time = task_sum.get(taskname, 0.0)
                tmp_sum_time = tmp_sum_time + tasktime
                task_sum[taskname] = tmp_sum_time
            current_date += timedelta(days=1)

        print(task_sum)
