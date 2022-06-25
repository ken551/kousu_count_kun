import tkinter as tk

# ウィンドウサイズ設定
WINDOW_STANDBY_WIDTH = 400
WINDOW_STANDBY_HEIGHT = 300
WINDOW_COUNTING_WIDTH = 160
WINDOW_COUNTING_HEIGHT = 120

def startCounting():
    root.geometry(f"{WINDOW_COUNTING_WIDTH}x{WINDOW_COUNTING_HEIGHT}")
    # ステータスバー表示
    root.overrideredirect(1)
    isStatusBarShown = False
    # 最前面固定
    root.attributes("-topmost", True)
    frameCounting.tkraise()

def stopCounting():
    root.geometry(f"{WINDOW_STANDBY_WIDTH}x{WINDOW_STANDBY_HEIGHT}")
    # ステータスバー表示
    root.overrideredirect(0)
    isStatusBarShown = True
    # 最前面固定解除
    root.attributes("-topmost", False)
    frameStandby.tkraise()

def onExit():
    root.destroy()

if __name__ == '__main__':
    root = tk.Tk() 
    root.geometry(f"{WINDOW_STANDBY_WIDTH}x{WINDOW_STANDBY_HEIGHT}")
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

    frameCounting.place(x=0, y=0)
    frameStandby.place(x=0, y=0)
    frameStandby.tkraise()
    root.mainloop() 