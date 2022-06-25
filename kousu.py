import tkinter as tk
from tkinter import messagebox
from datetime import *

# ウィンドウサイズ設定
WINDOW_STANDBY_WIDTH = 400
WINDOW_STANDBY_HEIGHT = 300
WINDOW_COUNTING_WIDTH = 160
WINDOW_COUNTING_HEIGHT = 120

SYSTEM_FONT_FAMILY = "Arial"
SYSTEM_FONT_SIZE = 30

def startCounting():
    global labelTime
    global isCounting
    global timeCountStarted
    global taskName

    root.geometry(f"{WINDOW_COUNTING_WIDTH}x{WINDOW_COUNTING_HEIGHT}")
    # ステータスバー表示
    root.overrideredirect(1)
    isStatusBarShown = False
    # 最前面固定
    root.attributes("-topmost", True)
    frameCounting.tkraise()

    # 現在時刻を取得
    timeCountStarted = datetime.now()

    timeNow = datetime.now()
    labelTime["text"] = timeNow.strftime("00:00:00")
    isCounting = True
    taskName = entryTaskName.get()
    root.after(500, refreshCounter)

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
    


def stopCounting():
    global isCounting

    root.geometry(f"{WINDOW_STANDBY_WIDTH}x{WINDOW_STANDBY_HEIGHT}")
    # ステータスバー表示
    root.overrideredirect(0)
    # 最前面固定解除
    root.attributes("-topmost", False)
    frameStandby.tkraise()
    isCounting = False

    timeDiff = datetime.now() - timeCountStarted
    hour, amari = divmod(timeDiff.seconds, 3600)
    min, sec = divmod(amari, 60)
    messagebox.showinfo("stop", f"作業:{taskName}\n稼働時間は{hour}時間{min}分です")

def onExit():
    root.destroy()

if __name__ == '__main__':
    root = tk.Tk() 
    root.geometry(f"{WINDOW_STANDBY_WIDTH}x{WINDOW_STANDBY_HEIGHT}")

    isColonDisplayed = True
    timeCountStarted = datetime.now()
    isCounting = False
    taskName = ""

    # 待機状態のフレーム
    frameStandby = tk.Frame(root, width=WINDOW_STANDBY_WIDTH, height=WINDOW_STANDBY_HEIGHT)
    isStatusBarShown = True
    btnToggleStatusBar = tk.Button(frameStandby, text="開始", command=startCounting)
    btnToggleStatusBar.place(x=160,y=70)
    buttonExit = tk.Button(frameStandby,text="exit", command=onExit)
    buttonExit.place(x=0,y=0)
    entryTaskName = tk.Entry(frameStandby, width=30)
    entryTaskName.place(x=10, y=40)

    # カウント状態のフレーム
    frameCounting = tk.Frame(root, width=WINDOW_COUNTING_WIDTH, height=WINDOW_COUNTING_HEIGHT)
    buttonStop = tk.Button(frameCounting, text="停止", command=stopCounting )
    buttonStop.place(x=0,y=0)
    labelTime = tk.Label(frameCounting, text="00:00", font=f"{SYSTEM_FONT_FAMILY} {SYSTEM_FONT_SIZE}", anchor="n")
    labelTime.place(x=0,y=50)

    frameCounting.place(x=0, y=0)
    frameStandby.place(x=0, y=0)
    frameStandby.tkraise()
    root.mainloop() 