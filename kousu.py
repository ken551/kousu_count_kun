import tkinter as tk
import datetime

# ウィンドウサイズ設定
WINDOW_STANDBY_WIDTH = 400
WINDOW_STANDBY_HEIGHT = 300
WINDOW_COUNTING_WIDTH = 160
WINDOW_COUNTING_HEIGHT = 120

SYSTEM_FONT_FAMILY = "Arial"
SYSTEM_FONT_SIZE = 30

def startCounting():
    root.geometry(f"{WINDOW_COUNTING_WIDTH}x{WINDOW_COUNTING_HEIGHT}")
    # ステータスバー表示
    root.overrideredirect(1)
    isStatusBarShown = False
    # 最前面固定
    root.attributes("-topmost", True)
    frameCounting.tkraise()

    global labelTime
    timeNow = datetime.datetime.now()
    labelTime["text"] = timeNow.strftime("%H:%I:%S")
    root.after(500, refreshCounter)

def refreshCounter():

    global isColonDisplayed
    if isColonDisplayed:
        labelTime["text"] = datetime.datetime.now().strftime("%H %I %S")
        isColonDisplayed = False
    else:
        labelTime["text"] = datetime.datetime.now().strftime("%H:%I:%S")
        isColonDisplayed = True
    root.after(500, refreshCounter)
    


def stopCounting():
    root.geometry(f"{WINDOW_STANDBY_WIDTH}x{WINDOW_STANDBY_HEIGHT}")
    # ステータスバー表示
    root.overrideredirect(0)
    # 最前面固定解除
    root.attributes("-topmost", False)
    frameStandby.tkraise()

def onExit():
    root.destroy()

if __name__ == '__main__':
    root = tk.Tk() 
    root.geometry(f"{WINDOW_STANDBY_WIDTH}x{WINDOW_STANDBY_HEIGHT}")

    isColonDisplayed = True

    # 待機状態のフレーム
    frameStandby = tk.Frame(root, width=WINDOW_STANDBY_WIDTH, height=WINDOW_STANDBY_HEIGHT)
    isStatusBarShown = True
    btnToggleStatusBar = tk.Button(frameStandby, text="開始", command=startCounting)
    btnToggleStatusBar.place(x=10,y=10)
    buttonExit = tk.Button(frameStandby,text="exit", command=onExit)
    buttonExit.place(x=100,y=100)

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