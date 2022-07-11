import tkinter as tk
from tkinter import messagebox
from datetime import *
import csv
import os

# ウィンドウサイズ設定
WINDOW_STANDBY_WIDTH = 400
WINDOW_STANDBY_HEIGHT = 250
WINDOW_COUNTING_WIDTH = 160
WINDOW_COUNTING_HEIGHT = 120

SYSTEM_FONT_FAMILY = "Arial"
SYSTEM_TIME_FONT_SIZE = 30
SYSTEM_NORMAL_FONT_SIZE = 8

FOLDER_NAME = "csvs"

def startCounting(taskNameArg):
    global labelTime
    global isCounting
    global timeCountStarted
    global taskName
    global taskNameHistory
    global taskNameHistoryTop

    root.geometry(f"{WINDOW_COUNTING_WIDTH}x{WINDOW_COUNTING_HEIGHT}")
    # ステータスバー表示
    root.overrideredirect(1)
    isStatusBarShown = False
    # 最前面固定
    # root.attributes("-topmost", True)
    frameCounting.tkraise()

    # 現在時刻を取得
    timeCountStarted = datetime.now()

    timeNow = datetime.now()
    labelTime["text"] = timeNow.strftime("00:00:00")
    isCounting = True
    taskName = taskNameArg # entryTaskName.get()
    labelTaskName["text"] = taskName
    taskNameHistory[taskNameHistoryTop] = taskName
    taskNameHistoryTop = (taskNameHistoryTop + 1) % 5

    # 時刻更新を500ms後に予約
    root.after(500, refreshCounter)

def startCountingFromHistory(i):
    def x(my_i = i):
        startCounting(labelTaskHistory[i]["text"])
    return x

def refreshCounter():

    global isColonDisplayed
    global timeCountStarted

    # 現在時刻を取得
    timeDiff = datetime.now()  - timeCountStarted
    hour, amari = divmod(timeDiff.seconds, 3600)
    min, sec = divmod(amari, 60 )

    if isColonDisplayed:
        labelTime["text"] = f"{str(hour).zfill(2)} {str(min).zfill(2)} {str(sec).zfill(2)}"
        isColonDisplayed = False
    else:
        labelTime["text"] = f"{str(hour).zfill(2)}:{str(min).zfill(2)}:{str(sec).zfill(2)}"
        isColonDisplayed = True
    if isCounting:
        root.after(500, refreshCounter)
    
def refreshTaskHistories():
    global taskNameHistory
    global taskNameHistoryTop
    for i in range(5):
        taskNameHistoryTop = 4 if (taskNameHistoryTop == 0) else (taskNameHistoryTop-1)
        labelTaskHistory[i]["text"] = taskNameHistory[taskNameHistoryTop]

def stopCounting():
    global isCounting

    root.geometry(f"{WINDOW_STANDBY_WIDTH}x{WINDOW_STANDBY_HEIGHT}")
    # ステータスバー表示
    root.overrideredirect(0)
    # 最前面固定解除
    # root.attributes("-topmost", False)
    frameStandby.tkraise()
    isCounting = False
    refreshTaskHistories()
    timeCountEnd = datetime.now()

    timeDiff = timeCountEnd - timeCountStarted
    hour, amari = divmod(timeDiff.seconds, 3600)
    min, sec = divmod(amari, 60)
    messagebox.showinfo("stop", f"作業:{taskName}\n稼働時間は{hour}時間{min}分です")
    try:
        #　CSVへの書き込み
        with open(f"{FOLDER_NAME}/{dateStr}.csv", mode="a", newline="") as f:
            data = [[taskName, (hour + min/60), timeCountStarted.strftime("%H:%M"), timeCountEnd.strftime("%H:%M")]]
            writer = csv.writer(f)
            writer.writerows(data)
    except PermissionError as e:
        # ファイル開いてる等で書き込み失敗の場合
        with open(f"{FOLDER_NAME}/tmp/{dateStr}_tmp.csv", mode="w", newline="") as f:
            data = [[taskName, (hour + min/60), timeCountStarted.strftime("%H:%M"), timeCountEnd.strftime("%H:%M")]]
            writer = csv.writer(f)
            writer.writerows(data)
        messagebox.showinfo("error", f"ファイル書き込みに失敗しました。（他のアプリでcsvファイルを開いていませんか？）\n tmp/{dateStr}_tmp.csv に今の記録を書き出したので、手動でマージしてください。")
   

def onExit():
    root.destroy()

if __name__ == '__main__':
    root = tk.Tk() 
    root.geometry(f"{WINDOW_STANDBY_WIDTH}x{WINDOW_STANDBY_HEIGHT}")

    isColonDisplayed = True
    timeCountStarted = datetime.now()
    isCounting = False
    taskName = ""
    taskNameHistory = [0]*5
    taskNameHistoryTop = 0
    dateStr = timeCountStarted.strftime("%Y%m%d")

    kousuList = None

    root.attributes("-topmost", True)

    # 待機状態のフレーム
    frameStandby = tk.Frame(root, width=WINDOW_STANDBY_WIDTH, height=WINDOW_STANDBY_HEIGHT)
    isStatusBarShown = True
    buttonExit = tk.Button(frameStandby,text="exit", command=onExit)
    buttonExit.place(x=0,y=0)
    entryTaskName = tk.Entry(frameStandby, width=35)
    entryTaskName.place(x=10, y=40)
    labelTaskHistory = [0] * 5
    btnTaskHistory = [0] * 5
    for i in range(5):
        labelTaskHistory[i] = tk.Label(frameStandby, text="-")
        labelTaskHistory[i].place(x=10, y=120+20*i)
        btnTaskHistory[i] = tk.Button(frameStandby, text="開始", command=startCountingFromHistory(i))
        btnTaskHistory[i].place(x=200, y=120+20*i)
    
    btnToggleStatusBar = tk.Button(frameStandby, text="開始", command=(lambda: startCounting(entryTaskName.get())))
    btnToggleStatusBar.place(x=160,y=70)


    # カウント状態のフレーム
    frameCounting = tk.Frame(root, width=WINDOW_COUNTING_WIDTH, height=WINDOW_COUNTING_HEIGHT)
    buttonStop = tk.Button(frameCounting, text="停止", command=stopCounting )
    buttonStop.place(x=0,y=0)
    labelTime = tk.Label(frameCounting, text="00:00", font=f"{SYSTEM_FONT_FAMILY} {SYSTEM_TIME_FONT_SIZE}", anchor="n")
    labelTime.place(x=0,y=50)
    labelTaskName = tk.Label(frameCounting, text="", font=f"{SYSTEM_FONT_FAMILY} {SYSTEM_NORMAL_FONT_SIZE}")
    labelTaskName.place(x=10,y=25)

    frameCounting.place(x=0, y=0)
    frameStandby.place(x=0, y=0)
    frameStandby.tkraise()

    # csvの存在確認
    if os.path.isfile(f'{FOLDER_NAME}/{dateStr}.csv'):
        print("file exists")
        with open(f"{FOLDER_NAME}/{dateStr}.csv", mode='r', newline='') as f:
            csvReader = csv.reader(f)
            kousuList = list(csvReader)
            print(kousuList)
    else:
        print("file not exists")
        # CSV読み込み
        header = ["タスク名","作業時間", "開始時刻", "終了時刻"]
        with open(f'{FOLDER_NAME}/{dateStr}.csv', mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)

    root.mainloop()