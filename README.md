# VideoFrameWithWorker

Check worker video with frame

git clone https://github.com/nkawa/VideoFrameWithWorker.git

cd VideoFrameWithWorker

python VideoCheck.py [video-file.mp4]

ビデオファイルは必ず指定してください。

上記で、ウィンドウが開いたら、まず json file を読み込んでください。
現状は、
　"adjusted_tracking_result_2023-12-05_28800_32400.json"

を開いてください。ここからは、基本的に "next"　ボタン、もしくは、 下のスライダーで
動かすことができます。

画像内のヒトの枠をクリックすると、右側の”Set”の上の値が入りますが、
ここは、まだ実装していません。
（予定としては、特定の ID を別の ID に変更する、といったことができると良いと思っています）

修正後のデータは別名で保存すると良いと思うので、その部分も作成が必要です。
