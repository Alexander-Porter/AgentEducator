from abc import ABC, abstractmethod
from flask import current_app
import os
import subprocess
import json
try:
    import whisper
except ImportError:
    whisper = None

class ASREngine(ABC):
    @abstractmethod
    def perform_asr(self, video_path):
        """对视频执行ASR处理，返回识别结果列表"""
        pass

class WhisperASREngine(ASREngine):
    def __init__(self, model_name="base"):
        if whisper is None:
            current_app.logger.error("Whisper库未安装，无法进行ASR处理")
            self.model = None
        else:
            try:
                self.model = whisper.load_model(model_name)
            except Exception as e:
                current_app.logger.error(f"加载Whisper模型失败: {e}")
                self.model = None

    def perform_asr(self, video_path):
        if not self.model:
            return None
        audio_path = video_path.replace('.mp4', '.wav')
        try:
            cmd = f"ffmpeg -i \"{video_path}\" -ab 160k -ac 2 -ar 44100 -vn \"{audio_path}\""
            subprocess.call(cmd, shell=True)
        except Exception as e:
            current_app.logger.error(f"提取音频失败: {e}")
            return None
        try:
            result = self.model.transcribe(
                audio_path,
                fp16=False,
                verbose=True
            )
            segments = result.get("segments", [])
        except Exception as e:
            current_app.logger.error(f"语音识别出错: {e}")
            segments = []
        finally:
            if os.path.exists(audio_path):
                os.remove(audio_path)
        return segments

class JsonASREngine(ASREngine):
    def perform_asr(self, video_path):
        """从视频同名JSON文件读取字幕信息"""
        json_path = video_path.replace('.mp4', '.json')
        
        if not os.path.exists(json_path):
            current_app.logger.error(f"JSON文件不存在: {json_path}")
            return None
            
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            body = data.get('body', [])
            segments = []
            
            for item in body:
                segment = {
                    'start': item.get('from', 0),
                    'end': item.get('to', 0),
                    'text': item.get('content', ''),
                    'id': item.get('sid', 0)
                }
                segments.append(segment)
            
            current_app.logger.info(f"成功从JSON文件读取 {len(segments)} 个字幕段落")
            return segments
            
        except Exception as e:
            current_app.logger.error(f"读取JSON文件失败: {e}")
            return None

