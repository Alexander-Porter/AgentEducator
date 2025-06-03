import os
import subprocess
import shutil
import cv2
from PIL import Image
import imagehash

def extract_keyframes(video_path, output_folder, similarity_threshold=0.9):
    """
    从视频中提取相似度去重的 I 帧关键帧
    """
    os.makedirs(output_folder, exist_ok=True)
    
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    temp_iframe_dir = os.path.join(output_folder, "iframes_temp")
    os.makedirs(temp_iframe_dir, exist_ok=True)

    # 用 ffmpeg 提取所有 I 帧（关键帧）
    ffmpeg_cmd = f'ffmpeg -i "{video_path}" -vf "select=\'eq(pict_type\\,I)\'" -vsync vfr -frame_pts 1 -q:v 2 "{temp_iframe_dir}/iframe_%08d.jpg"'
    try:
        subprocess.run(ffmpeg_cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"ffmpeg 提取 I 帧失败: {str(e)}")
        return [], 0, 0

    # 获取视频基本信息
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()

    # 加载 I 帧图像
    iframe_files = sorted([f for f in os.listdir(temp_iframe_dir) if f.endswith('.jpg')])
    if not iframe_files:
        print("未提取到 I 帧")
        return [], fps, total_frames

    keyframes_data = []
    previous_hash = None
    keyframe_index = 1

    for i, filename in enumerate(iframe_files):
        filepath = os.path.join(temp_iframe_dir, filename)
        image = Image.open(filepath)
        current_hash = imagehash.phash(image)

        # 判断是否保留该帧
        should_save = False
        if previous_hash is None:
            should_save = True
        else:
            diff = previous_hash - current_hash
            similarity = 1 - diff / current_hash.hash.size
            if similarity < similarity_threshold:
                should_save = True

        if should_save:
            # 尝试解析帧号
            frame_num_str = filename.replace("iframe_", "").replace(".jpg", "")
            try:
                frame_num = int(frame_num_str)
            except ValueError:
                frame_num = i * int(total_frames / len(iframe_files))
            
            # 计算时间点
            time_point = frame_num / fps if fps > 0 else 0
            time_formatted = f"{int(time_point // 60):02d}:{int(time_point % 60):02d}.{int((time_point % 1) * 100):02d}"

            # 重命名并保存
            new_filename = f"{video_name}_keyframe_{keyframe_index}_{frame_num}.jpg"
            new_filepath = os.path.join(output_folder, new_filename)
            shutil.copy2(filepath, new_filepath)

            keyframes_data.append({
                "id": keyframe_index,
                "frame_number": frame_num,
                "time_point": round(time_point, 3),
                "time_formatted": time_formatted,
                "file_name": new_filename
            })
            keyframe_index += 1
            previous_hash = current_hash

    # 清理临时目录
    shutil.rmtree(temp_iframe_dir)

    return keyframes_data, fps, total_frames
kf_info, fps, total = extract_keyframes("E:/AgentEducator/backend/temp_video/f870dec22bbc41f18897928233ce2ebf_-_36_0402--2.5.32--_87__720P_921_NTc.mp4", "output_keyframes", similarity_threshold=0.9)
print(f"提取关键帧数量: {len(kf_info)}")
for kf in kf_info:
    print(kf["time_formatted"], kf["file_name"])
