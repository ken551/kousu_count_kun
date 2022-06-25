import tkinter as tk

def toggleStatusBar():
    global isStatusBarShown
    if isStatusBarShown:
        # ステータスバー表示
        root.overrideredirect(1)
        isStatusBarShown = False
        # 最前面固定
        root.attributes("-topmost", True)
    else:
        # ステータスバー表示
        root.overrideredirect(0)
        isStatusBarShown = True
        # 最前面固定解除
        root.attributes("-topmost", False)

def onExit():
    root.destroy()

if __name__ == '__main__':
    root = tk.Tk() 
    isStatusBarShown = True
    # ステータスバー非表示
    root.overrideredirect(0)
    btnToggleStatusBar = tk.Button(root, text="i am a button", command=toggleStatusBar)
    btnToggleStatusBar.place(x=10,y=10)
    btnExit = tk.Button(root,text="exit", command=onExit)
    btnExit.place(x=100,y=100)
    root.mainloop() 