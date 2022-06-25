import tkinter as tk

# ウィンドウサイズ設定
WINDOW_STANDBY_WIDTH = 400
WINDOW_STANDBY_HEIGHT = 300
WINDOW_COUNTING_WIDTH = 200
WINDOW_COUNTING_HEIGHT = 150

def toggleStatusBar():
    global isStatusBarShown
    if isStatusBarShown:
        root.geometry(f"{WINDOW_COUNTING_WIDTH}x{WINDOW_COUNTING_HEIGHT}")
        # ステータスバー表示
        root.overrideredirect(1)
        isStatusBarShown = False
        # 最前面固定
        root.attributes("-topmost", True)
    else:
        root.geometry(f"{WINDOW_STANDBY_WIDTH}x{WINDOW_STANDBY_HEIGHT}")
        # ステータスバー表示
        root.overrideredirect(0)
        isStatusBarShown = True
        # 最前面固定解除
        root.attributes("-topmost", False)

def onExit():
    root.destroy()

if __name__ == '__main__':
    root = tk.Tk() 
    root.geometry(f"{WINDOW_STANDBY_WIDTH}x{WINDOW_STANDBY_HEIGHT}")
    isStatusBarShown = True
    btnToggleStatusBar = tk.Button(root, text="i am a button", command=toggleStatusBar)
    btnToggleStatusBar.place(x=10,y=10)
    btnExit = tk.Button(root,text="exit", command=onExit)
    btnExit.place(x=100,y=100)
    
    root.mainloop() 