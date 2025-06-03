"""
ASR处理模块
负责处理视频的语音识别，并将结果分配给关键帧
"""

import os
import subprocess
import shutil
from flask import current_app
from utils.asr_engine import WhisperASREngine,JsonASREngine

class ASRProcessor:
    """ASR处理器类"""
    
    def __init__(self, asr_engine=None):
        """
        初始化ASR处理器
        
        参数:
            asr_engine: ASR引擎实例，默认为None，将使用Whisper引擎
        """
        self.asr_engine = asr_engine or WhisperASREngine()
        
    def perform_asr(self, video_path):
        """
        对视频进行语音识别
        
        参数:
            video_path: 视频文件路径
            
        返回:
            ASR结果列表
        """
        json_path = video_path.replace('.mp4', '.json')
        if os.path.exists(json_path):
            self.asr_engine=JsonASREngine()
        return self.asr_engine.perform_asr(video_path)
    
    def assign_asr_to_keyframes(self, keyframes_data, asr_result):
        """
        将ASR结果分配给对应的关键帧
        
        参数:
            keyframes_data: 关键帧数据列表
            asr_result: ASR结果列表
            
        返回:
            处理后的关键帧数据列表
        """
        if not asr_result:
            return keyframes_data
        
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
                last_frame_before_speech["asr_texts_raw"].append(segment)
            elif sorted_keyframes:
                # 如果所有关键帧都在语音段之后，分配给第一个关键帧
                sorted_keyframes[0]["asr_texts_raw"].append(segment)
        
        # 生成每个关键帧的ASR文本
        for frame in keyframes_data:
            # 将ASR文本提取到asr_texts列表中
            frame["asr_texts"] = "  ".join([item["text"] for item in frame["asr_texts_raw"]])
        
        return keyframes_data