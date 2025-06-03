import json
import cv2
from skimage.metrics import structural_similarity as ssim
import os
import time
import argparse
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import sys

import loguru
logger = loguru.logger

def is_significant_change(frame1, frame2, threshold=0.90):
    """
    计算结构相似性（SSIM），判断当前帧与前一帧是否有较大变化
    """
    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
    score, _ = ssim(gray1, gray2, full=True)
    return score < threshold  # 低于阈值，说明变化明显

def process_frame_block_animate(frames, start_prev_frame=None, fine_step=10, threshold=0.90):
    """
    处理一块视频帧，同时检测动画段：
      - 当连续检测到帧有较大变化时，将它们收集到一个动画段列表中
      - 当首次遇到不变化的帧时，对动画段以 fine_step 检查
          如果在该动画段中每隔 fine_step 帧仍然保持变化，则认为是动画区间，
          只取该段最后一帧；否则，将动画段内的帧全部保留。
    参数:
      frames: [(frame_index, frame), ...] 列表
      start_prev_frame: 前一块最后一帧（用于跨块比较），默认为 None
      fine_step: 在动画段内检查变化的步长（默认 10 帧）
      threshold: SSIM 阈值
    返回:
      keyframes: [(frame_index, frame), ...] 关键帧列表
    """
    keyframes = []
    prev_frame = start_prev_frame
    animation_segment = []  # 收集连续变化的帧
    in_animation = False

    for frame_count, frame in frames:
        changed = (prev_frame is None) or is_significant_change(prev_frame, frame, threshold)
        if changed:
            # 处于变化状态，加入动画段
            animation_segment.append((frame_count, frame))
            in_animation = True
        else:
            # 当前帧未发生明显变化
            if in_animation:
                # 检查动画段是否在 finer 步长下持续变化
                fine_changed = True
                if len(animation_segment) > 1:
                    for i in range(0, len(animation_segment) - 1, fine_step):
                        # 若相邻采样帧未达到显著变化，则认为动画段不连续
                        if not is_significant_change(animation_segment[i][1], animation_segment[i+1][1], threshold):
                            fine_changed = False
                            break
                if fine_changed and len(animation_segment) > 0:
                    # 动画段确认：只保留该段最后一帧
                    keyframes.append(animation_segment[-1])
                else:
                    # 普通情况：保留整个动画段的所有关键帧
                    keyframes.extend(animation_segment)
                animation_segment = []  # 清空动画段
                in_animation = False
            # 对于当前未变化的帧，也作为独立关键帧保留
            #keyframes.append((frame_count, frame))
        prev_frame = frame

    # 如果块结束时还在动画段中，则同样处理
    if in_animation and len(animation_segment) > 0:
        fine_changed = True
        if len(animation_segment) > 1:
            for i in range(0, len(animation_segment) - 1, fine_step):
                if not is_significant_change(animation_segment[i][1], animation_segment[i+1][1], threshold):
                    fine_changed = False
                    break
        if fine_changed:
            keyframes.append(animation_segment[-1])
        else:
            keyframes.extend(animation_segment)

    return keyframes

def process_ocr(keyframes_data, output_folder):
    """
    对关键帧进行OCR处理，提取文字信息
    """
    try:
        from cnocr import CnOcr
        ocr = CnOcr()
    except ImportError:
        logger.error("cnocr库未安装，请使用pip install cnocr安装")
        return keyframes_data
    
    logger.info("正在进行OCR文字识别...")
    for frame_info in tqdm(keyframes_data, desc="OCR处理"):
        image_path = os.path.join(output_folder, frame_info["file_name"])
        try:
            result = ocr.ocr(image_path)
            # 提取识别到的文本
            texts = []
            
            # 处理OCR结果，将ndarray转换为普通列表以便JSON序列化
            serializable_result = []
            for item in result:
                if isinstance(item, dict) and 'position' in item and 'text' in item:
                    # 将ndarray转换为普通列表
                    position_list = item['position'].tolist() if hasattr(item['position'], 'tolist') else item['position']
                    
                    # 创建可序列化的字典
                    serializable_item = {
                        'position': position_list,
                        'score': float(item['score']) if 'score' in item else 0.0,
                        'text': item['text']
                    }
                    serializable_result.append(serializable_item)
                    
                    # 添加文本到结果列表
                    texts.append(item['text'])
            
            # 将处理后的可序列化结果替代原始结果
            result = serializable_result
            
            # 将OCR结果添加到关键帧信息中
            frame_info["ocr_result"] = texts
            frame_info["ocr_result_raw"] = result
        except Exception as e:
            logger.error(f"处理图片 {image_path} 时出错: {str(e)}")
            frame_info["ocr_result"] = []
            
    return keyframes_data

def process_asr(video_path):
    """
    对视频进行语音识别，使用OpenAI Whisper模型
    """
    try:
        import whisper
        import subprocess
    except ImportError:
        logger.error("Whisper库未安装，请使用pip install openai-whisper安装")
        return None
        
    # 检查ffmpeg是否可用
    import shutil
    if not shutil.which("ffmpeg"):
        logger.error("未找到ffmpeg，请确保已安装ffmpeg并添加到系统PATH中")
        return None
    
    # 提取音频
    logger.info("正在从视频中提取音频...")
    audio_path = video_path.replace('.mp4', '.wav')
    try:
        command = f"ffmpeg -i \"{video_path}\" -ab 160k -ac 2 -ar 44100 -vn \"{audio_path}\""
        subprocess.call(command, shell=True)
    except Exception as e:
        logger.error(f"提取音频失败: {str(e)}")
        return None
    
    logger.info("正在进行语音识别...")
    asr_result = ""
    
    try:
        # 加载Whisper模型
        model = whisper.load_model("medium")  # 可选: tiny, base, small, medium, large
        
        # 预先检测语言（可选，让Whisper更好地准备模型）
        #detected_language = whisper.detect_language(audio_path,mel=False)
        #lang_code = "zh" if "zh" in detected_language else None
        #logger.info(f"检测到语言: {detected_language}")
        
        # 执行语音识别
        result = model.transcribe(
            audio_path,
            fp16=False,  # 某些Windows环境下fp16可能导致问题
            verbose=True
        )
        
        # 获取识别结果
        asr_result = result["segments"]
        logger.info(f"语音识别完成，结果长度: {len(asr_result)}")
        
        # 删除提取的音频文件
        os.remove(audio_path)
    except Exception as e:
        logger.error(f"语音识别过程中出错: {str(e)}")
        if os.path.exists(audio_path):
            os.remove(audio_path)
    
    return asr_result

def assign_asr_to_keyframes(keyframes_data, asr_result):
    """
    将ASR结果分配给对应的关键帧
    对于每段语音，找到最后一个时间点小于语音开始时间的关键帧，将该语音添加到该关键帧的asr_texts_raw列表中
    这符合PPT演示场景：先切换到幻灯片，然后开始讲解该幻灯片的内容
    """
    if not asr_result:
        return keyframes_data
    
    logger.info("正在将ASR结果分配到对应的关键帧...")
    
    # 初始化每个关键帧的ASR文本列表
    for frame in keyframes_data:
        frame["asr_texts_raw"] = []
    
    # 按照时间点给关键帧排序
    sorted_keyframes = sorted(keyframes_data, key=lambda x: x["time_point"])
    
    # 遍历每个ASR结果，分配到对应的关键帧
    for segment in asr_result:
        asr_start_time = segment["start"]
        
        # 找到最后一个时间点小于语音开始时间的关键帧
        last_frame_before_speech = None
        for frame in sorted_keyframes:
            if frame["time_point"] <= asr_start_time:
                last_frame_before_speech = frame
            else:
                break
        
        # 分配语音段到对应的关键帧
        if last_frame_before_speech:
            # 将语音分配给语音开始前的最后一个关键帧
            last_frame_before_speech["asr_texts_raw"].append(segment)
        elif sorted_keyframes:
            # 如果没有找到合适的关键帧（视频最开始的语音），则分配给第一帧
            sorted_keyframes[0]["asr_texts_raw"].append(segment)
    for frame in keyframes_data:
        # 将ASR文本提取到asr_texts列表中
        frame["asr_texts"] = "  ".join([item["text"] for item in frame["asr_texts_raw"]])
    logger.info("ASR结果分配完成")
    return keyframes_data

def extract_key_frames(video_path, output_folder, num_threads=8, frame_skip=5, fine_step=10, threshold=0.90, 
                      enable_ocr=False, enable_asr=False):
    """
    1. 按照 frame_skip 参数从视频中读取帧，并存入列表
    2. 将帧列表均分为多个连续块，每块的首帧比较时使用前一帧（从原始帧列表中获取）
    3. 多线程并行处理各块，提取关键帧（加入动画段检测逻辑）
    4. 合并各块结果，排序并简单去重后保存到 output_folder 文件夹中
    5. 根据需要进行OCR和ASR处理
    """
    os.makedirs(output_folder, exist_ok=True)

    # 获取视频文件名（不包含扩展名）
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    
    logger.info(f"正在处理视频: {video_path}")
    logger.info(f"输出目录: {output_folder}")
    
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    frames_list = []
    frame_count = 0
    success, frame = cap.read()
    while success:
        if frame_count % frame_skip == 0:
            frames_list.append((frame_count, frame))
        frame_count += 1
        success, frame = cap.read()
    cap.release()

    num_frames = len(frames_list)
    # 将帧列表均分为 num_threads 块
    chunk_size = num_frames // num_threads
    blocks = []
    for i in range(num_threads):
        start_index = i * chunk_size
        # 最后一块包含所有剩余的帧
        end_index = num_frames if i == num_threads - 1 else (i + 1) * chunk_size
        blocks.append(frames_list[start_index:end_index])

    # 确定每个块的初始上一帧
    start_prev_frames = []
    for i in range(num_threads):
        if i == 0:
            start_prev_frames.append(None)
        else:
            # 用当前块起始帧前的那一帧作为比较基准
            start_prev_frames.append(frames_list[i * chunk_size - 1][1])

    keyframes_results = []
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = []
        for i in range(num_threads):
            futures.append(executor.submit(process_frame_block_animate, 
                                             blocks[i], 
                                             start_prev_frames[i],
                                             fine_step,
                                             threshold))
        for future in tqdm(futures, desc="处理视频帧"):
            keyframes_results.extend(future.result())

    # 按帧序号排序
    keyframes_results.sort(key=lambda x: x[0])

    # 简单去重：若相邻关键帧帧号差小于 fps/2，则认为重复，只保留第一个
    unique_keyframes = []
    if keyframes_results:
        unique_keyframes.append(keyframes_results[0])
        for i in range(1, len(keyframes_results)):
            if keyframes_results[i][0] - unique_keyframes[-1][0] > fps / 2:
                unique_keyframes.append(keyframes_results[i])

    keyframes_data = []
    for i, (frame_num, frame) in enumerate(unique_keyframes):
        # 生成文件名
        output_filename = f"keyframe_{i+1}_{frame_num}.jpg"
        output_path = os.path.join(output_folder, output_filename)
        cv2.imwrite(output_path, frame)
        
        # 计算时间点（秒）
        time_point = frame_num / fps
        
        # 添加关键帧信息到JSON数据
        keyframes_data.append({
            "id": i + 1,
            "frame_number": int(frame_num),
            "time_point": float(time_point),
            "time_formatted": f"{int(time_point // 60):02d}:{int(time_point % 60):02d}.{int((time_point % 1) * 100):02d}",
            "file_name": output_filename
        })
    
    # OCR处理
    if enable_ocr:
        logger.info("启用OCR处理")
        keyframes_data = process_ocr(keyframes_data, output_folder)
    
    # ASR处理
    asr_result = None
    if enable_asr:
        logger.info("启用ASR处理")
        asr_result = process_asr(video_path)
        # 如果成功获取ASR结果，则将结果分配给对应的关键帧
        if asr_result:
            keyframes_data = assign_asr_to_keyframes(keyframes_data, asr_result)
    
    # 准备最终JSON数据
    json_data = {
        "video_name": video_name,
        "total_frames": int(total_frames),
        "fps": float(fps),
        "keyframes_count": len(keyframes_data),
        "keyframes": keyframes_data
    }
    
    if enable_asr and asr_result:
        json_data["asr_result"] = asr_result
    
    # 保存JSON文件，使用视频名作为文件名
    json_path = os.path.join(output_folder, f"{video_name}.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=4)
    
    logger.info(f"提取了 {len(unique_keyframes)} 张关键帧")
    logger.info(f"JSON数据已保存至: {json_path}")
    
    return json_path

def binary_search_change_point(frames, start_idx, end_idx, prev_frame, threshold):
    """
    使用二分查找确定场景变化的精确位置
    
    参数:
      frames: 视频帧列表，格式为 [(frame_index, frame), ...]
      start_idx: 起始索引（场景未变化）
      end_idx: 结束索引（场景已变化）
      prev_frame: 用于比较的前一帧
      threshold: 相似度阈值
      
    返回:
      change_idx: 变化点的索引
    """
    while start_idx < end_idx - 1:
        mid_idx = (start_idx + end_idx) // 2
        mid_frame = frames[mid_idx][1]
        
        if is_significant_change(prev_frame, mid_frame, threshold):
            end_idx = mid_idx
        else:
            start_idx = mid_idx
            
    return end_idx

def process_adaptive_frame_block(frames, start_prev_frame=None, initial_step=8, threshold=0.90):
    """
    使用自适应采样处理一块视频帧，减少比较操作次数
    
    参数:
      frames: [(frame_index, frame), ...] 列表
      start_prev_frame: 前一块最后一帧，默认为 None
      initial_step: 初始采样步长，默认为 60
      fine_step: 详细检查的步长，默认为 10
      threshold: SSIM 阈值
      
    返回:
      keyframes: [(frame_index, frame), ...] 关键帧列表
    """
    if not frames:
        return []
        
    keyframes = []
    prev_frame = start_prev_frame
    n = len(frames)
    
    # 第一帧总是关键帧（如果没有前置帧）
    if prev_frame is None and n > 0:
        keyframes.append(frames[0])
        prev_frame = frames[0][1]
    
    i = 0
    while i < n:
        # 自适应步长，从大步长开始
        step = initial_step
        
        # 尝试跳跃比较
        change_found = False
        next_i = min(i + step, n - 1)
        
        while next_i < n:
            # 检查当前帧和跳跃后的帧是否有明显变化
            if i < n and next_i < n and is_significant_change(prev_frame, frames[next_i][1], threshold):
                # 找到变化点，使用二分查找确定精确位置
                change_idx = binary_search_change_point(frames, i, next_i, prev_frame, threshold)
                
                # 添加变化点为关键帧
                keyframes.append(frames[change_idx])
                prev_frame = frames[change_idx][1]
                i = change_idx + 1
                change_found = True
                break
            
            # 如果没有找到变化，继续增大步长
            i = next_i
            next_i = min(i + step, n - 1)
            step *= 2  # 倍增步长
            
            # 防止步长过大导致错过太多帧
            if step > n // 4:
                step = n // 4
                if step < 1:
                    step = 1
        
        # 如果找到了变化点，继续从该点开始检测
        if change_found:
            continue
            
        # 如果到达序列末尾且没有变化，结束循环
        if i >= n - 1:
            break
            
        # 处理剩余帧
        i += 1
    
    return keyframes

def extract_adaptive_key_frames(video_path, output_folder, num_threads=8, frame_skip=5, 
                            initial_step=8, fine_step=10, threshold=0.90, 
                            enable_ocr=False, enable_asr=False):
    """
    使用自适应采样策略提取关键帧，减少比较操作次数
    """
    os.makedirs(output_folder, exist_ok=True)

    # 获取视频文件名（不包含扩展名）
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    
    logger.info(f"正在处理视频: {video_path}")
    logger.info(f"输出目录: {output_folder}")
    logger.info(f"使用自适应采样策略，初始步长: {initial_step}")
    
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # 采样帧
    frames_list = []
    frame_count = 0
    success, frame = cap.read()
    while success:
        if frame_count % frame_skip == 0:
            frames_list.append((frame_count, frame))
        frame_count += 1
        success, frame = cap.read()
    cap.release()

    num_frames = len(frames_list)
    logger.info(f"共采样 {num_frames} 帧进行处理")
    
    # 将帧列表均分为 num_threads 块
    chunk_size = num_frames // num_threads
    blocks = []
    for i in range(num_threads):
        start_index = i * chunk_size
        # 最后一块包含所有剩余的帧
        end_index = num_frames if i == num_threads - 1 else (i + 1) * chunk_size
        blocks.append(frames_list[start_index:end_index])

    # 确定每个块的初始上一帧
    start_prev_frames = []
    for i in range(num_threads):
        if i == 0:
            start_prev_frames.append(None)
        else:
            # 用当前块起始帧前的那一帧作为比较基准
            start_prev_frames.append(frames_list[i * chunk_size - 1][1])

    keyframes_results = []
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = []
        for i in range(num_threads):
            futures.append(executor.submit(process_adaptive_frame_block, 
                                         blocks[i], 
                                         start_prev_frames[i],
                                         initial_step,
                                         fine_step,
                                         threshold))
        for future in tqdm(futures, desc="处理视频帧"):
            keyframes_results.extend(future.result())

    # 按帧序号排序
    keyframes_results.sort(key=lambda x: x[0])

    # 简单去重：若相邻关键帧帧号差小于 fps/2，则认为重复，只保留第一个
    unique_keyframes = []
    if keyframes_results:
        unique_keyframes.append(keyframes_results[0])
        for i in range(1, len(keyframes_results)):
            if keyframes_results[i][0] - unique_keyframes[-1][0] > fps / 2:
                unique_keyframes.append(keyframes_results[i])

    # 处理并保存关键帧
    keyframes_data = []
    for i, (frame_num, frame) in enumerate(unique_keyframes):
        # 生成文件名
        output_filename = f"keyframe_{i+1}_{frame_num}.jpg"
        output_path = os.path.join(output_folder, output_filename)
        cv2.imwrite(output_path, frame)
        
        # 计算时间点（秒）
        time_point = frame_num / fps
        
        # 添加关键帧信息到JSON数据
        keyframes_data.append({
            "id": i + 1,
            "frame_number": int(frame_num),
            "time_point": float(time_point),
            "time_formatted": f"{int(time_point // 60):02d}:{int(time_point % 60):02d}.{int((time_point % 1) * 100):02d}",
            "file_name": output_filename
        })
    
    # OCR处理
    if enable_ocr:
        logger.info("启用OCR处理")
        keyframes_data = process_ocr(keyframes_data, output_folder)
    
    # ASR处理
    asr_result = None
    if enable_asr:
        logger.info("启用ASR处理")
        asr_result = process_asr(video_path)
        # 如果成功获取ASR结果，则将结果分配给对应的关键帧
        if asr_result:
            keyframes_data = assign_asr_to_keyframes(keyframes_data, asr_result)
    
    # 准备最终JSON数据
    json_data = {
        "video_name": video_name,
        "total_frames": int(total_frames),
        "fps": float(fps),
        "keyframes_count": len(keyframes_data),
        "keyframes": keyframes_data,
        "extraction_method": "adaptive_sampling",
        "initial_step": initial_step,
        "threshold": threshold
    }
    
    if enable_asr and asr_result:
        json_data["asr_result"] = asr_result
    
    # 保存JSON文件，使用视频名作为文件名
    json_path = os.path.join(output_folder, f"{video_name}.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=4)
    
    logger.info(f"提取了 {len(unique_keyframes)} 张关键帧")
    logger.info(f"JSON数据已保存至: {json_path}")
    
    return json_path

def parse_arguments():
    """
    解析命令行参数
    """
    parser = argparse.ArgumentParser(description="视频关键帧提取工具")
    parser.add_argument("video_path", help="视频文件路径")
    parser.add_argument("-o", "--output", help="输出目录路径", default="keyframes_output")
    parser.add_argument("-t", "--threads", type=int, default=8, help="处理线程数")
    parser.add_argument("-s", "--skip", type=int, default=100, help="帧采样间隔")
    parser.add_argument("-f", "--fine", type=int, default=10, help="动画检测细粒度")
    parser.add_argument("--threshold", type=float, default=0.98, help="结构相似性阈值(0-1)")
    parser.add_argument("--ocr", action="store_true", help="启用OCR文字识别")
    parser.add_argument("--asr", action="store_true", help="启用ASR语音识别")
    parser.add_argument("--adaptive", action="store_true", help="使用自适应采样算法")
    parser.add_argument("--initial-step", type=int, default=60, help="自适应采样初始步长")
    return parser.parse_args()

def main():
    """
    主函数
    """
    args = parse_arguments()
    
    # 检查视频文件是否存在
    if not os.path.exists(args.video_path):
        logger.error(f"视频文件不存在: {args.video_path}")
        return 1
    
    start_time = time.time()
    
    try:
        # 根据参数选择使用传统方法还是自适应方法
        if args.adaptive:
            json_path = extract_adaptive_key_frames(
                args.video_path, 
                args.output, 
                num_threads=args.threads,
                frame_skip=args.skip,
                initial_step=args.initial_step,
                fine_step=args.fine,
                threshold=args.threshold,
                enable_ocr=args.ocr,
                enable_asr=args.asr
            )
        else:
            json_path = extract_key_frames(
                args.video_path, 
                args.output, 
                num_threads=args.threads,
                frame_skip=args.skip,
                fine_step=args.fine,
                threshold=args.threshold,
                enable_ocr=args.ocr,
                enable_asr=args.asr
            )
    except Exception as e:
        logger.exception(f"处理过程中出错: {str(e)}")
        return 1
    
    end_time = time.time()
    logger.info(f"总运行时间: {end_time - start_time:.2f} 秒")
    return 0

if __name__ == '__main__':
    sys.exit(main())
