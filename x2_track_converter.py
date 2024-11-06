

# 2xのビデオに対応するため、 track 番号を 半分にする
# とりあえず奇数は無視しちゃう（ごめん。本当は統合すべき）

# 書き出しは統合 pkl にしちゃう（高速化）

import json
import pickle
import pandas as pd


def load_json_file(file):
    with open(file, 'r') as f:
        workers = json.load(f)

    new_frame = []

    for frame in workers:
        if frame['frame_id'] % 2 != 0:
            continue
        frame['frame_id']=frame['frame_id']//2 # 1フレームずらしてみる?       
        new_frame.append(frame)

    return new_frame

def load_box(file):
    box_df = pd.read_csv(file)
    boxes = []
    for i in range(4500):
        sub_df = list(box_df[box_df['frame_id'] == i]['pred_result'])
        print("Length of sub_df", len(sub_df),i)
        boxes.append(sub_df)
    return boxes



def save_track_file(file, workers,pallets,boxes):
    with open(file, 'wb') as f:
        pickle.dump({'workers': workers, 'pallets': pallets, 'boxes':boxes}, f)

def doit():
#    workers = load_json_file('1101tracking_result_20241003_worker_body_1100_1200_updated.json')
#    workers = load_json_file("tracking_result_20241003_worker_body_1100_1200_with_bibs_v8x_updated.json")
#    workers = load_json_file("adjusted_tracking_result_2024-10-03_39600_43200_200_99_90_True_150_200_200_9990_10_True_90.json")
    workers = load_json_file("modify_adjusted_tracking_result_2024-10-03_39600_43200_200_99_90_True_150_200_200_9985_10_True_90.json")
    pallets = load_json_file('tracking_result_20241003_pallet_085_1100_1200_updated.json')
    boxes = load_box('2024-10-03_1100_1200_2x_frame.csv')

    save_track_file('track_2x_20241106_bibs_ymori_true.pkl', workers, pallets,boxes)


if __name__ == '__main__':
    doit()
