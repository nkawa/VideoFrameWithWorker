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

# パレットの正解データも対応できるように！


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

# 拡大表示のサイズ
kw = 300
kh = 300

def change_size(event):
        w = app.canvas.winfo_width()
        h = app.canvas.winfo_height()
#        print("Change",w,h)

class App(tk.Frame):
    def __init__(self,master = None):
        super().__init__(master)
        self.workers = None
        self.current_id = -1
        self.pallet_id = -1
        self.image_frame = tk.Frame(self.master)
        self.button_frame = tk.Frame(self.master)
        self.track_info_frame = tk.Frame(self.master)
        self.json_sub = tk.Frame(self.button_frame)
        self.set_frame = tk.Frame(self.button_frame)
        self.slider_frame = tk.Frame(self.track_info_frame)
        self.button_sub = tk.Frame(self.button_frame)

        self.canvas = tk.Canvas(self.image_frame, width = cw, height = ch)
#        self.canvas.bind('<Button-1>', self.canvas_click)
        self.canvas.pack(expand = True, fill = tk.BOTH, anchor=tk.CENTER, padx=10)

        self.kakudai = tk.Canvas(self.button_frame, width = kw, height = kh)
#        self.kakudai.delete("all")
        self.kakudai.pack(expand = True, fill=tk.X, anchor=tk.CENTER,padx=2,pady=2)
        self.kakudai.create_rectangle(0, 0, kw, kh, fill="black", outline="")


        self.csv_file = tk.Label(self.button_frame, text = "JSON: Not set")
        self.csv_file.pack(expand = True, padx=10, pady=10)

        self.csv_button2 = tk.Button(self.json_sub, text="Palette JSON", command=self.openPalletJSON, width=10)
        self.csv_button2.pack(expand = True, side=tk.LEFT,padx=10)
        self.csv_button = tk.Button(self.json_sub, text="ID_JSON", command=self.openJSON, width=10)
        self.csv_button.pack(expand = True, side=tk.LEFT,padx=10 )
        self.json_sub.pack(expand = True,  padx=10)

        self.check_frame = tk.Frame(self.button_frame)
        self.cframe = tk.BooleanVar(value=True)
        self.cpallet = tk.BooleanVar(value=True)
        self.check_pallet = tk.Checkbutton(self.check_frame, text="Pallet" ,width=10,variable = self.cpallet)
        self.check_pallet.pack(side=tk.LEFT,padx=10)
        self.check_track = tk.Checkbutton(self.check_frame, text="Show Track", width=10,variable = self.cframe)
        self.check_track.pack(side=tk.LEFT,padx=10)
        self.check_frame.pack(expand = True, fill = tk.X, padx=10, pady=10)

# IDを登録する仕組み！
        self.id_box = tk.Label(self.button_sub,text="ID:  0       Subj:  ")
        self.id_box.pack(side=tk.LEFT,padx=0,pady=10)
        self.subj_box = tk.Entry(self.button_sub,width=15)
        self.subj_box.insert(tk.END,"")
        self.subj_box.pack(side=tk.LEFT, padx=0,pady=10)
        self.button_sub.pack(expand = True, fill = tk.X, padx=10, pady=10)
        self.id_button = tk.Button(self.set_frame,text="Set", command=self.set_id,width=10)
        self.id_button.pack(side=tk.LEFT,padx=10)

        self.cid_button = tk.Button(self.set_frame,text="Change From Here", command=self.change_from,width=15)
        self.cid_button.pack(side=tk.LEFT,padx=10)
        self.set_frame.pack(padx=10, pady=10)

        self.track_frame = tk.Frame(self.button_frame)
        self.sid_button = tk.Button(self.track_frame,text="Search TrackID", command=self.search_trackid,width=15)
        self.sid_button.pack(side=tk.LEFT,padx=10)

        self.cinfo_button = tk.Button(self.track_frame,text="Clear TrackInfo", command=self.clear_track_info,width=15)
        self.cinfo_button.pack(side=tk.LEFT, padx=10)
        self.track_frame.pack(padx=10, pady=10)


        self.save_frame = tk.Frame(self.button_frame)
        self.save_button = tk.Button(self.save_frame, text="Save PalJSON", command=self.save_pal_json)
        self.save_button.pack(side=tk.LEFT,padx=10)

        self.save_button2 = tk.Button(self.save_frame, text="Save JSON", command=self.save_json)
        self.save_button2.pack(side=tk.LEFT,padx=10)
        self.save_frame.pack( padx=10, pady=10)

        self.pallet_id_frame = tk.Frame(self.button_frame)
        self.pallet_id_label = tk.Label(self.pallet_id_frame,text="PID: 0")
        self.pallet_id_label.pack(side=tk.LEFT,padx=10)
        self.pallet_id_box = tk.Entry(self.pallet_id_frame,width=10)
        self.pallet_id_box.pack(side=tk.LEFT,padx=10)
        self.pallet_set = tk.Button(self.pallet_id_frame, text="set", command=self.set_pallet_id)
        self.pallet_set.pack(side=tk.LEFT,padx=10)
        self.pallet_id_frame.pack(padx=10, pady=10)

        self.pal_edit_frame = tk.Frame(self.button_frame)
        self.pal_line = tk.Button(self.pal_edit_frame, text="Check_Line", command=self.check_id_line)
        self.pal_line.pack(side=tk.LEFT,padx=10)
        self.pal_edit_frame.pack(padx=10, pady=10)


        self.frame_num = tk.Label(self.button_frame,text="<-Frame:_")
        self.frame_num.pack(expand=True, fill= tk.X, padx = 10, pady = 10)

        self.frameVar = tk.IntVar()

        self.track_info = tk.Canvas(self.track_info_frame, width = 1400, height = 10)
        self.track_info.pack(expand = True, fill = tk.X, anchor=tk.CENTER, padx=10,pady=0)
        self.track_info.create_rectangle(0, 0, 1400, 10, fill="black", outline="")

        self.slider = tk.Scale(self.slider_frame, 
                               variable=self.frameVar,
                               command=self.scroll,
                               from_=0, to=17999,length=1400, orient=HORIZONTAL)
        self.ssd = 0
        self.sed = 17999
        self.scl = int(90/7)
        self.slider.pack(side=tk.LEFT,expand = True, fill = tk.X, padx=10, pady=0)
        self.splus1 = tk.Button(self.slider_frame, text="1", width=10,command=self.speedOne)
        self.splus1.pack(side=tk.LEFT, padx=10 )
        self.splus5 = tk.Button(self.slider_frame, text="5",  width=10,command=self.speed5)
        self.splus5.pack(side=tk.LEFT, padx=10 )
#        self.splus20 = tk.Button(self.slider_frame, text="20", command=self.speed20)
#        self.splus20.pack(side=tk.LEFT)
        self.splusF = tk.Button(self.slider_frame, text="F",  width=10,command=self.speedF)
        self.splusF.pack(side=tk.LEFT, padx=10 )


        self.slider_frame.pack(expand = True, fill = tk.X,pady=0)


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
        self.track_info_frame.grid(column=0,row=2, columnspan=2)
#        self.slider_frame.grid(column=0,row=2, columnspan=2)

        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_rowconfigure(1, weight=1)
        self.master.grid_columnconfigure(0, weight=1)
        self.master.grid_columnconfigure(1, weight=1)
        

        self.canvas.bind("<ButtonPress-1>", self.check_id)

        self.master.bind('<Configure>', change_size)

    def speedOne(self):
        st = self.frameVar.get()-400
        if st < 0:
            st = 0
        ed = st+1400
        if ed > 17999:
            ed = 17999
        self.ssd = st
        self.sed = ed
        self.scl = 1
        self.slider.config(from_ = st,to = ed)

    def speed5(self):
        st = self.frameVar.get()-400*5
        if st < 0:
            st = 0
        ed = st+1400*5
        if ed > 17999:
            ed = 17999
        self.ssd = st
        self.sed = ed
        self.scl = 5
        self.slider.config(from_ = st,to = ed)

    def speedF(self):
        st = 0
        ed = 17999
        self.ssd = st
        self.sed = ed
        self.scl = int(90/7)
        self.slider.config(from_ = st,to = ed)



    def current_tracks(self):
        if self.current_id >= 0:
            return self.workers, self.current_id
        if self.pallet_id >= 0:
            return self.pallets,  self.pallet_id
        return None,0

    def current_color(self):
        if self.current_id >= 0:
            return self.track_colors[self.current_id]
        if self.pallet_id >= 0:
            return self.ptrack_colors[self.pallet_id]
        return 0,0,0

 # 現在得られているTrack ID を track_info に表示する
    def search_trackid(self):
        frames,cid = self.current_tracks()
        if frames is None:
            return
        for frame in frames:
            for track in frame['tracks']:
                if track['track_id'] == cid:
                    fid = frame['frame_id']

                    r,g,b = self.current_color()
                    color = f"#{r:02x}{g:02x}{b:02x}"
                    x = int((fid- self.ssd)/self.scl )
                    if x < 0: 
                        continue
                    if x > self.sed:
                        break
                    self.track_info.create_line(x, 0, x, 10,fill=color)

#現在得られているTrack ID の移動線をFrame に描画する
    def check_id_line(self):
        frames,cid = self.current_tracks()
        if frames is None:
            return
        lastx,lasty = -1,-1
        for frame in frames:
            for track in frame['tracks']:
                if track['track_id'] == cid:
                    fid = frame['frame_id']
                    r,g,b = self.current_color()
                    color = f"#{r:02x}{g:02x}{b:02x}"

                    x0,y0,width,height = track['bbox']
                    xx = int((x0- BASE_X+width/2)*SCALE*cscale)
                    yy = int((y0- BASE_Y+height/2)*SCALE*cscale)
                    if lastx == -1:
                        lastx,lasty = xx,yy
                    else:
                        self.canvas.create_line(lastx, lasty, xx,yy,fill=color)
                        lastx,lasty = xx,yy
                        



    def clear_track_info(self):
        self.track_info.delete("all")
        self.track_info.create_rectangle(0, 0, 1400, 10, fill="black", outline="")


    def show_kakudai(self):
        #self.current_id から 拡大イメージの表示
        if self.current_id < 0:
            return
        frameData = self.workers[self.frameVar.get()]
        for w in frameData['tracks']:
            if w['track_id'] == self.current_id:
                x0,y0,width,height = w['bbox']
                xx = int((x0- BASE_X)*SCALE)
                yy = int((y0- BASE_Y)*SCALE)
                width *= SCALE
                height *= SCALE        

                boximage = self.base_image[yy-10:yy+int(height)+10, xx-10:xx+int(width)+10]

                aspect = boximage.shape[1] / boximage.shape[0]
                if aspect > kw/kh :
                    boximage = cv2.resize(boximage,dsize=(kw,int(kw/aspect)))
                else:
                    boximage = cv2.resize(boximage,dsize=(int(kh*aspect),kh))

                pil3_image = Image.fromarray(boximage)
                # ガベージコレクションされないようにすべきだった！！！！！
                self.photo_image = ImageTk.PhotoImage(pil3_image)
                    
                self.kakudai.delete("all")
                self.kakudai.create_image(
                        int(kw/2),int(kh/2),
                        anchor=tk.CENTER,
                        image=self.photo_image  # 表示画像データ
                )



# check_id
    def check_id(self,event):
        x = int(event.x / cscale)
        y = int(event.y / cscale)
#        print("Click",x,y)
        not_found = True
        if self.workers is not None:
            frameData = self.workers[self.frameVar.get()]
            for w in frameData['tracks']:
                x0,y0,width,height = w['bbox']
                xx = int((x0- BASE_X)*SCALE)
                yy = int((y0- BASE_Y)*SCALE)
                width *= SCALE
                height *= SCALE
                if xx < x and x < xx+width and yy < y and y < yy+height:
#                    print(w['track_id'],x0,y0,"-",xx,yy)
                    self.id_box["text"]="ID: "+str(w['track_id'])+"      Subj: "
                    self.current_id = w['track_id']
                    self.show_kakudai()

#                    print("Show image",photo_image,pil_image.size)
#                    popup = tk.Toplevel(self.master)
#                    popup.title("Track ID:"+str(w['track_id']))
#                    popup.geometry("400x400")
#                    label = tk.Label(popup, image=photo_image)
#                    label.pack()

                    not_found = False

                    if 'subj_id' in w :
                        self.subj_box.delete(0,tk.END)
                        self.subj_box.insert(tk.END,w['subj_id'])
                    else:
                        self.subj_box.delete(0,tk.END)
                    break

        if self.pallets is not None and not_found:
            fnum = self.frameVar.get()
            for frameData in self.pallets:
                if frameData['frame_id'] == fnum:
                    for w in frameData['tracks']:
                        x0,y0,width,height = w['bbox']
                        xx = int((x0- BASE_X)*SCALE)
                        yy = int((y0- BASE_Y)*SCALE)
                        width *= SCALE
                        height *= SCALE
                        if xx < x and x < xx+width and yy < y and y < yy+height:
#                       print(w['track_id'],x0,y0,"-",xx,yy)
                            self.pallet_id = w['track_id']
                            self.current_id = -1 #pallet セレクト時は、current_id は無効
                            self.pallet_id_label["text"]="Pal: "+str(w['track_id'])
                        
                            if 'subj_id' in w :
                                self.pallet_id_box.delete(0,tk.END)
                                self.pallet_id_box.insert(tk.END,w['subj_id'])
                            else:
                                self.pallet_id_box.delete(0,tk.END)
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
            self.id_box["text"] = -1
            self.subj_box.delete(0,tk.END)

# pallet_id 対応
    def set_pallet_id(self):
        if self.pallet_id >= 0:
            
            subj_id = self.pallet_id_box.get()
            # すべての current_id を new_id に変更する
            for frame in self.workers:
                for track in frame['tracks']:
                    if track['track_id'] == self.pallet_id:
                        track['subj_id'] = subj_id
            self.pallet_id = -1
            self.pallet_id_label["text"] = "PID: -1"
            self.pallet_id_box.delete(0,tk.END)
        pass


# ある場所からID変更 対応
    def change_from(self):
        if self.current_id >= 0:
            subj_id = self.subj_box.get()
            # 現在の track　以降のcurrent_id に subj_id に変更する
            currentFrame = self.frameVar.get()
            for frame in self.workers:
                if frame['frame_id'] >= currentFrame:
                    for track in frame['tracks']:
                        if track['track_id'] == self.current_id:
                            track['subj_id'] = subj_id
            self.current_id = -1
            self.id_box["text"] = -1
            self.subj_box.delete(0,tk.END)

# save_json 対応
    def save_json(self):
        path = filedialog.asksaveasfilename(defaultextension=".json",filetypes=[("JSON","*.json")],title="Save JSON file")
        print(path)
        if len(path)>0:
            with open(path, 'w') as file:
                json.dump(self.workers,file)
                print("Saved",path)

    def save_pal_json(self):
        path = filedialog.asksaveasfilename(defaultextension=".json",filetypes=[("JSON","*.json")],title="Save Pallete JSON file")
        print(path)
        if len(path)>0:
            with open(path, 'w') as file:
                json.dump(self.paleets,file)
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

    def openPalletJSON(self):
        path = filedialog.askopenfilename(defaultextension=".json",filetypes=[("JSON","*.json")],title="Open Pallet JSON file")
#        self.csv_file["text"]="JSON:"+path
        self.csv_file["text"]="PJSON:loaded"
        if len(path)>0:
            with open(path, 'r') as file:
                self.pallets = json.load(file)
                print("loaded",len(self.pallets))
                self.ptrack_colors = {track['track_id']: generate_random_color() for frame in self.pallets for track in frame['tracks']}
                #self.next() # 画像出す！

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
        self.base_image = base_image.copy()
              
#        cv_image = cv2.cvtColor(dst, cv2.COLOR_BGR2RGB)
        ## ここで、他のデータも重ねて書く！
        if self.workers is not None and self.cframe.get():
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

        if self.pallets is not None and self.cpallet.get():
            for frameData in self.pallets:
                if frameData['frame_id'] == frame:
                    for w in frameData['tracks']:
#                        print(w)
                        x0,y0,width,height = w['bbox']
                        xx = int((x0- BASE_X)*SCALE)
                        yy = int((y0- BASE_Y)*SCALE)
                        width *= SCALE
                        height *= SCALE
                        color = self.ptrack_colors[w['track_id']]

                        label_text = "p"+str(w['track_id'])
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
        
        self.show_kakudai()
    
#        print("Show image",tf)        

    
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Video TrackCheker 2024-10-03") 
    app = App(master=root)
    app.cap = cv2.VideoCapture(sys.argv[1])
    app.frame =0
    print(app.cap, sys.argv[1])
    app.mainloop()

