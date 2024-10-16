import cv2

from tkinter import *
from PIL import Image, ImageTk, ImageOps  # 画像データ用
import sys
import tkinter as tk
from tkinter import filedialog
import glob
import pandas as pd
from pathlib import Path
import json
import random

# 2024-10-03 実験のトラッキング対応づけ用ツール
# stich の仕組みが違うため、位置の計算の変更が必要
# 元データが、3990x2312 ピクセルの動画で、縮小動画は 1280x742ピクセル
# 元のトラッキングの位置から、 3885.36, 812.703 シフトさせると、元の動画の位置になる。これを 1280x742 に変換
# 1280/3990 = 0.321303

BASE_X = 3885.36
BASE_Y = 812.703
SCALE = 0.321303

#　ビブスの色と合わせると良い



def ts2sec(tstr):
    h = int(tstr[:-6])
    m = int(tstr[-5:-3])
    s = int(tstr[-2:])
    return h*3600+m*60+s
def sec2ts(sec):
    s = sec%60
    m = int(sec/60)%60
    h = int(sec/3600)
    return "{:02d}{:02d}{:02d}".format(h,m,s)

def sec2ts2(sec):
    s = sec%60
    m = int(sec/60)%60
    h = int(sec/3600)
    return "{:02d}:{:02d}:{:02d}".format(h,m,s)

# 時刻の先頭に 0　を追加するだけ。
def add_recog_0(x):
    return ("0"+x)[-8:]

def read_timestamp(fname):
    df = pd.read_csv(fname, usecols=[0,1,2,3,4])
    df['recog']=df['recog'].map(add_recog_0)
    df['sec']= df['recog'].map(ts2sec)
    return df

def check_timestamp(df):
    ldiff = df['sec'][0]
    error_index = []
    for i,row in df.iterrows():
        diff = row['sec']
        if ldiff +1 != diff and ldiff !=diff:
            print(i,"vid",row['vid_idx'],"frm",row['frm_idx'],lstr,ldiff,row['recog'],diff)
            error_index.append(i)
        lstr = row['recog']
        ldiff = diff

    return error_index


colors ={
    "パレット":(255,255,0),
    'パレット（定点）':(240,250,0), 
    "スリムカート":(200,200,100),
    'スリムカート（定点）':(200,200,100),
    "台車":(240,200,200),
    '台車（定点）':(240,200,0), 
    "オリコン":(240,0,0),
    'かご車（定点）':(200,200,100), 
    '床':(200,200,100),
    '-':(200,200,100)
}

# ランダムのシードを固定したい
random.seed(0)

# ランダムカラーを生成する関数
def generate_random_color():
    r = [random.uniform(0, 1) for _ in range(3)]
    return (int(r[0]*255),int(r[1]*255),int(r[2]*255))


cscale = 1.2
cw = int(1280*cscale)
ch = int(742*cscale)

def change_size(event):
        w = app.canvas.winfo_width()
        h = app.canvas.winfo_height()
#        print("Change",w,h)

class App(tk.Frame):
    def __init__(self,master = None):
        super().__init__(master)
        self.workers = None
        self.current_id = -1
        self.image_frame = tk.Frame(self.master)
        self.slider_frame = tk.Frame(self.master)
        self.button_frame = tk.Frame(self.master)
        self.button_sub = tk.Frame(self.button_frame)

        self.canvas = tk.Canvas(self.image_frame, width = cw, height = ch)
#        self.canvas.bind('<Button-1>', self.canvas_click)
        self.canvas.pack(expand = True, fill = tk.BOTH, anchor=tk.CENTER, padx=10)

        self.id_box = tk.Label(self.button_sub,text="ID:  0       Subj:  ")
        self.id_box.pack(side=tk.LEFT,padx=0,pady=10)
        self.subj_box = tk.Entry(self.button_sub,width=15)
        self.subj_box.insert(tk.END,"")
        self.subj_box.pack(side=tk.LEFT, padx=0,pady=10)
        self.button_sub.pack(expand = True, fill = tk.X, padx=10, pady=10)
        self.id_button = tk.Button(self.button_frame,text="Set", command=self.set_id,width=10)
        self.id_button.pack(padx=10,pady=10)

        self.csv_file = tk.Label(self.button_frame, text = "JSON: Not set")
        self.csv_file.pack(expand = True, padx=10, pady=10)

        self.csv_button = tk.Button(self.button_frame, text="Open JSON", command=self.openJSON, width=40)
        self.csv_button.pack(expand = True, fill = tk.X, padx=10, pady=10)

        self.save_button = tk.Button(self.button_frame, text="Save JSON", command=self.save_json)
        self.save_button.pack(expand = True, padx=10, pady=10)


        self.frame_num = tk.Label(self.button_frame,text="<-Frame:_")
        self.frame_num.pack(expand=True, fill= tk.X, padx = 10, pady = 10)

        self.frameVar = tk.IntVar()

        self.slider = tk.Scale(self.slider_frame, 
                               variable=self.frameVar,
                               command=self.scroll,
                               from_=0, to=17999,length=1400, orient=HORIZONTAL)
        self.slider.pack(expand = True, fill = tk.X, padx=10, pady=10)

        self.num = tk.Entry(self.button_frame,width=10)
        self.num.insert(tk.END,"0")  
        self.num.pack(padx=10,pady=10)
#        self.num.place(x=820, y=70)
        self.back_button = tk.Button(self.button_frame, text="Back", command=self.back, width=40)
        self.back_button.pack(expand = True, fill = tk.X, padx=10, pady=10)

        self.go_button = tk.Button(self.button_frame, text="Next", command=self.next, width=40)
        self.go_button.pack(expand = True, fill = tk.X, padx=10, pady=10)


        self.image_frame.grid(column=0, rowspan=2)
        self.button_frame.grid(column=1, row=1)
        self.slider_frame.grid(column=0,row=2, columnspan=2)

        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_rowconfigure(1, weight=1)
        self.master.grid_columnconfigure(0, weight=1)
        self.master.grid_columnconfigure(1, weight=1)
        

        self.canvas.bind("<ButtonPress-1>", self.check_id)

        self.master.bind('<Configure>', change_size)


# check_id
    def check_id(self,event):
        x = int(event.x / cscale)
        y = int(event.y / cscale)
        print("Click",x,y)
        if self.workers is not None:
            frameData = self.workers[self.frameVar.get()]
            for w in frameData['tracks']:
                x0,y0,width,height = w['bbox']
                xx = int((x0- BASE_X)*SCALE)
                yy = int((y0- BASE_Y)*SCALE)
                width *= SCALE
                height *= SCALE
                if xx < x and x < xx+width and yy < y and y < yy+height:
                    print(w['track_id'],x0,y0,"-",xx,yy)
                    self.id_box["text"]="ID: "+str(w['track_id'])+"      Subj: "
                    self.current_id = w['track_id']
                    if 'subj_id' in w :
                        self.subj_box.delete(0,tk.END)
                        self.subj_box.insert(tk.END,w['subj_id'])
                    else:
                        self.subj_box.delete(0,tk.END)
                    break

# set id 対応
    def set_id(self):
        if self.current_id >= 0:
            
            subj_id = self.subj_box.get()
            # すべての current_id を new_id に変更する
            for frame in self.workers:
                for track in frame['tracks']:
                    if track['track_id'] == self.current_id:
                        track['subj_id'] = subj_id
            self.current_id = -1

# save_json 対応
    def save_json(self):
        path = filedialog.asksaveasfilename(defaultextension=".json",filetypes=[("JSON","*.json")],title="Save JSON file")
        print(path)
        if len(path)>0:
            with open(path, 'w') as file:
                json.dump(self.workers,file)
                print("Saved",path)
    
# slider 対応
    def scroll(self, event):
        global app
        frame = self.frameVar.get()
        self.num.delete(0,tk.END)  
        self.num.insert(tk.END,str(frame))  
        self.next()

    def openJSON(self):
        path = filedialog.askopenfilename(defaultextension=".json",filetypes=[("JSON","*.json")],title="Open JSON file")
        print(path)
#        self.csv_file["text"]="JSON:"+path
        self.csv_file["text"]="JSON:loaded"
        if len(path)>0:
            with open(path, 'r') as file:
                self.workers = json.load(file)
                print(len(self.workers))
                self.track_colors = {track['track_id']: generate_random_color() for frame in self.workers for track in frame['tracks']}
                self.next() # 画像出す！
#            df = read_timestamp(path)
#            check_timestamp(df)


    def openCSV(self):
        path = filedialog.askopenfilename(defaultextension=".csv",filetypes=[("CSV","*.csv")],title="Open csv file")
        print(path)
        self.csv_file["text"]="CSV:"+path
        if len(path)>0:
            df = read_timestamp(path)
            check_timestamp(df)

    def back(self):
        frame = int(self.num.get())-2
        if frame <0:
            frame = 0
        self.num.delete(0,tk.END)  
        self.num.insert(tk.END,str(frame))          
        self.next()

    def next(self):
        global app
        frame = int(self.num.get())
        self.frameVar.set(frame)
#        cap.
#        print("pushed next for ",frame)
        if app.frame != frame:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES,frame)
            app.frame = frame

        # 現在のフレーム番号
        rframe = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
        self.frame_num["text"] = "<----  Frame: "+str(rframe)+", try to set: "+str(frame)

        tf, img = self.cap.read()
        # 画像を半分のサイズにしたい
        if not tf:
#            print("Capture failed for",self.cap)
            return
        base_image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
              
#        cv_image = cv2.cvtColor(dst, cv2.COLOR_BGR2RGB)
        ## ここで、他のデータも重ねて書く！
        if self.workers is not None:
            frameData = self.workers[frame]
            for w in frameData['tracks']:
#                print(w)
                x0,y0,width,height = w['bbox']
                xx = int((x0- BASE_X)*SCALE)
                yy = int((y0- BASE_Y)*SCALE)
                width *= SCALE
                height *= SCALE
                color = self.track_colors[w['track_id']]
#                print(w['track_id'],x0,y0,"-",xx,yy)
                label_text = str(w['track_id'])
                if 'subj_id' in w:
                    label_text += ":"+w['subj_id']
                label_len = len(label_text)


                cv2.putText(base_image, text=label_text,org=(xx,yy-3*label_len),   
                    fontFace=cv2.FONT_HERSHEY_SIMPLEX,fontScale=0.7,color=color,thickness=1,lineType=cv2.LINE_4)
                
                base_image = cv2.rectangle(base_image,(int(xx),yy),(int(xx+width),int(yy+height)),color, thickness=2)

        cv_image = cv2.resize(base_image,dsize=(cw,ch))

        app.frame += 1
        
        self.num.delete(0,tk.END)  

        self.num.insert(tk.END,str(frame+1))  
        self.pil_image = Image.fromarray(cv_image)
        #pimg = tk.PhotoImage(image=pil_image)
        self.pimg  = ImageTk.PhotoImage(image=self.pil_image)
        self.canvas.delete("all")
        self.canvas.create_image(
                int(cw/2),       # 画像表示位置(Canvasの中心)
                int(ch/2),                   
                image=self.pimg  # 表示画像データ
                )
#        print("Show image",tf)        

    
if __name__ == "__main__":
    root = tk.Tk()
    app = App(master=root)
    app.cap = cv2.VideoCapture(sys.argv[1])
    app.frame =0
    print(app.cap, sys.argv[1])
    app.mainloop()
