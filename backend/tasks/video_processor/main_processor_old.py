"""
主处理器模块
负责协调所有视频处理模块，执行完整的视频处理流程
"""

import os
import uuid
from datetime import datetime
from flask import current_app
import cv2

# 导入数据库模型
from models.models import db, Video, VideoProcessingTask, VideoSummary
from models.models import VideoKeyframe, VideoVectorIndex

# 导入处理模块
from .keyframe_extractor import extract_keyframes
from .ocr_processor import OCRProcessor
from .asr_processor import ASRProcessor
from .vector_indexer import build_vector_index, check_vector_index_exists
from .summary_generator import generate_video_summary, generate_section_summary, group_keyframes_into_sections
from .db_handler import save_keyframes_to_db, load_keyframes_from_db, check_video_summary_exists
from .task_logger import add_task_log

# 配置信息
KEYFRAMES_OUTPUT_DIR = "temp_keyframes"
VECTOR_INDEX_DIR = "vector_indices"

def process_video_task(video_id, stop_flag=None, processing_steps=None, preview_mode=False):
    """
    处理视频任务的主函数
    
    参数:
        video_id: 视频ID
        stop_flag: 停止标志(threading.Event)，如果设置则中断处理
        processing_steps: 要执行的步骤列表，可包含：
            - "keyframes": 关键帧提取
            - "ocr": OCR文字识别
            - "asr": 语音识别
            - "vector": 向量索引构建
            - "summary": 视频摘要生成
        preview_mode: 预览模式，为True时不写入数据库，只写入TaskLog
    """
    try:
        # 获取视频信息
        video = Video.query.get(video_id)
        if not video:
            current_app.logger.error(f"视频不存在: {video_id}")
            return False
        
        # 1. 查找现有任务并更新状态为进行中
        task = VideoProcessingTask.query.filter_by(video_id=video_id, status="pending").first()
        if task:
            task_id = task.task_id
            task.status = "processing"
        else:
            # 如果没有找到待处理的任务，创建一个新任务
            task_id = f"task-{uuid.uuid4().hex[:8]}"
            task = VideoProcessingTask(
                video_id=video_id,
                task_id=task_id,
                status="processing",
                processing_type="all",
                start_time=datetime.now()
            )
            db.session.add(task)
            
        db.session.commit()
        add_task_log(task_id, video_id, 'debug', f"进程ID:{os.getpid()}")
        add_task_log(task_id, video_id, 'info', f"开始处理视频: {video.title}")
        
        # 根据参数决定是否清除旧数据
        if should_clear_old:
            add_task_log(task_id, video_id, 'info', "清除旧的处理数据，重新进行全流程处理")
            # 删除旧的关键帧数据和向量索引
            VideoKeyframe.query.filter_by(video_id=video_id).delete()
            VideoVectorIndex.query.filter_by(video_id=video_id).delete()
            VideoSummary.query.filter_by(video_id=video_id).delete()
            db.session.commit()
        else:
            add_task_log(task_id, video_id, 'info', "尝试使用已有数据进行处理")
            # 后续步骤将根据需要检查和使用已有数据
        
        # 2. 视频路径计算
        video_path = os.path.join(os.getcwd(), video.video_url.lstrip('/'))
        if not os.path.exists(video_path):
            add_task_log(task_id, video_id, 'error', f"视频文件不存在: {video_path}")
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        add_task_log(task_id, video_id, 'info', f"视频路径: {video_path}")
        
        # 检查是否请求停止
        if stop_flag and stop_flag.is_set():
            add_task_log(task_id, video_id, 'warning', "收到停止请求，任务被中断")
            task.status = 'cancelled'
            task.error_message = '任务被手动停止'
            task.end_time = datetime.now()
            db.session.commit()
            return False
        
        # 3. 创建输出目录
        output_folder = os.path.join(KEYFRAMES_OUTPUT_DIR, f"video_{video_id}")
        os.makedirs(output_folder, exist_ok=True)
        add_task_log(task_id, video_id, 'info', f"创建输出目录: {output_folder}")
        
        # 初始化变量
        keyframes_data = []
        fps = 0
        total_frames = 0
        
        # 尝试从数据库加载已有的关键帧数据（如果不清除旧数据）
        if not should_clear_old:
            keyframes_data = load_keyframes_from_db(video_id)
            if keyframes_data and len(keyframes_data) > 0:
                add_task_log(task_id, video_id, 'info', f"从数据库加载了 {len(keyframes_data)} 个关键帧数据")
                # 获取视频基本信息
                cap = cv2.VideoCapture(video_path)
                fps = cap.get(cv2.CAP_PROP_FPS)
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                cap.release()
                task.progress = 0.3
                db.session.commit()
        
        # 4. 提取关键帧（如果需要）
        if not keyframes_data or len(keyframes_data) == 0:
            add_task_log(task_id, video_id, 'info', "开始提取关键帧...")
            keyframes_data, fps, total_frames = extract_keyframes(video_path, output_folder,similarity_threshold=10)
            add_task_log(task_id, video_id, 'info', f"提取了 {len(keyframes_data)} 个关键帧, FPS: {fps}, 总帧数: {total_frames}")
            task.progress = 0.3
            db.session.commit()
        
        # 检查是否请求停止
        if stop_flag and stop_flag.is_set():
            add_task_log(task_id, video_id, 'warning', "收到停止请求，任务被中断")
            task.status = 'cancelled'
            task.error_message = '任务被手动停止'
            task.end_time = datetime.now()
            db.session.commit()
            return False
        
        # 5. OCR处理
        # 检查关键帧数据中是否已有OCR结果
        need_ocr = True
        if not should_clear_old:
            # 检查是否所有关键帧都有OCR结果
            for keyframe in keyframes_data:
                if "ocr_result" in keyframe and  keyframe["ocr_result"]:
                    need_ocr = False
                    break
        else:
            need_ocr = True  # 如果需要清除旧数据，则必须进行OCR处理
        
        if need_ocr:
            add_task_log(task_id, video_id, 'info', "开始OCR文字识别...")
            ocr_processor = OCRProcessor()
            keyframes_data = ocr_processor.perform_ocr(keyframes_data, output_folder)
            add_task_log(task_id, video_id, 'info', "OCR处理完成")
        else:
            add_task_log(task_id, video_id, 'info', "关键帧已有OCR结果，跳过OCR处理")
            
        task.progress = 0.5
        db.session.commit()
        
        # 检查是否请求停止
        if stop_flag and stop_flag.is_set():
            add_task_log(task_id, video_id, 'warning', "收到停止请求，任务被中断")
            task.status = 'cancelled'
            task.error_message = '任务被手动停止'
            task.end_time = datetime.now()
            db.session.commit()
            return False
        
        # 6. ASR处理
        # 检查关键帧数据中是否已有ASR结果
        need_asr = True
        if not should_clear_old:
            # 检查是否所有关键帧都有ASR结果
            for keyframe in keyframes_data:
                if "asr_texts"  in keyframe and keyframe["asr_texts"]:
                    need_asr = False
                    break
        else:
            need_asr = True  # 如果需要清除旧数据，则必须进行ASR处理
            
        if need_asr:
            add_task_log(task_id, video_id, 'info', "开始语音识别...")
            asr_processor = ASRProcessor()
            asr_result = asr_processor.perform_asr(video_path)
            if asr_result:
                add_task_log(task_id, video_id, 'info', f"语音识别成功，识别了 {len(asr_result)} 个语音片段")
                keyframes_data = asr_processor.assign_asr_to_keyframes(keyframes_data, asr_result)
            else:
                add_task_log(task_id, video_id, 'warning', "语音识别失败或没有可识别的语音")
        else:
            add_task_log(task_id, video_id, 'info', "关键帧已有ASR结果，跳过ASR处理")
            
        task.progress = 0.7
        db.session.commit()
        
        # 检查是否请求停止
        if stop_flag and stop_flag.is_set():
            add_task_log(task_id, video_id, 'warning', "收到停止请求，任务被中断")
            task.status = 'cancelled'
            task.error_message = '任务被手动停止'
            task.end_time = datetime.now()
            db.session.commit()
            return False
        
        # 7. 保存关键帧数据到数据库
        # 如果需要更新关键帧数据
        if need_ocr or need_asr or should_clear_old:

            VideoKeyframe.query.filter_by(video_id=video_id).delete()
            db.session.commit()
                
            add_task_log(task_id, video_id, 'info', "开始保存关键帧数据到数据库...")
            success = save_keyframes_to_db(video_id, keyframes_data)
            if not success:
                add_task_log(task_id, video_id, 'error', "保存关键帧数据到数据库失败")
                raise Exception("保存关键帧数据到数据库失败")
            add_task_log(task_id, video_id, 'info', "关键帧数据已保存到数据库")
        else:
            add_task_log(task_id, video_id, 'info', "使用已有的关键帧数据，不需要更新数据库")
        
        # 检查是否请求停止
        if stop_flag and stop_flag.is_set():
            add_task_log(task_id, video_id, 'warning', "收到停止请求，任务被中断")
            task.status = 'cancelled'
            task.error_message = '任务被手动停止'
            task.end_time = datetime.now()
            db.session.commit()
            return False
            
        # 8. 构建向量索引
        # 首先检查是否已有向量索引
        vector_exists = False
        if not should_clear_old:
            vector_exists, existing_index_path = check_vector_index_exists(video_id)
            
        if vector_exists:
            add_task_log(task_id, video_id, 'info', f"使用已有向量索引: {existing_index_path}")
            index_path = existing_index_path
        else:
            # 需要构建新的向量索引
            add_task_log(task_id, video_id, 'info', "开始构建向量索引...")
            
            # 如果要清除旧数据，先删除现有索引
            if should_clear_old:
                VideoVectorIndex.query.filter_by(video_id=video_id).delete()
                db.session.commit()
                
            index_path = os.path.join(VECTOR_INDEX_DIR, f"video_{video_id}")
            success = build_vector_index(video_id, keyframes_data, index_path)
            if success:
                add_task_log(task_id, video_id, 'info', f"向量索引构建成功，保存到 {index_path}")
                # 保存索引信息到数据库
                vector_index = VideoVectorIndex(
                    video_id=video_id,
                    index_path=index_path,
                    embedding_model="Pro/BAAI/bge-m3",
                    total_vectors=len(keyframes_data)
                )
                db.session.add(vector_index)
                db.session.commit()
            else:
                add_task_log(task_id, video_id, 'warning', "向量索引构建失败")
            
        # 检查是否请求停止
        if stop_flag and stop_flag.is_set():
            add_task_log(task_id, video_id, 'warning', "收到停止请求，任务被中断")
            task.status = 'cancelled'
            task.error_message = '任务被手动停止'
            task.end_time = datetime.now()
            db.session.commit()
            return False
        
        # 9. 生成视频摘要和关键词
        # 首先检查是否已有摘要
        summary_exists = False
        if not should_clear_old:
            summary_exists, existing_summary = check_video_summary_exists(video_id)
            
        if summary_exists:
            add_task_log(task_id, video_id, 'info', "使用已有视频摘要数据")
            summary_data = existing_summary
        else:
            # 需要生成新的摘要
            add_task_log(task_id, video_id, 'info', "开始生成视频摘要和关键词...")
            task.progress = 0.9
            db.session.commit()
            summary_data = generate_video_summary(video_id, keyframes_data, task_id)
            
            if summary_data:
                # 如果要清除旧数据或需要生成新摘要，先删除旧记录
                VideoSummary.query.filter_by(video_id=video_id).delete()
                db.session.commit()
                
                # 将关键帧分组成区间
                add_task_log(task_id, video_id, 'info', "将视频关键帧分组成区间...")
                
                # 使用增强的分段算法，提供更自然的区间划分
                sections_data = group_keyframes_into_sections(
                    keyframes_data,
                    max_section_duration=300,  # 5分钟
                    min_keyframes_per_section=2,
                    max_keyframes_per_section=15,
                    content_similarity_threshold=0.6
                )
                
                add_task_log(task_id, video_id, 'info', f"视频被分为 {len(sections_data)} 个区间")
                
                # 为每个区间生成摘要
                section_summaries = []
                for idx, section in enumerate(sections_data):
                    add_task_log(task_id, video_id, 'info', f"为区间 {idx+1}/{len(sections_data)} 生成摘要...")
                    
                    # 生成区间摘要
                    start_time = section["start_time"]
                    end_time = section["end_time"]
                    section_summary = generate_section_summary(
                        section, 
                        video.title, 
                        video.description if video.description else "", 
                        task_id, 
                        video_id
                    )
                    
                    # 计算区间时长
                    duration = end_time - start_time
                    minutes = int(duration // 60)
                    seconds = int(duration % 60)
                    duration_text = f"{minutes}分{seconds}秒" if minutes > 0 else f"{seconds}秒"
                    
                    section_summaries.append({
                        "title": f"区间 {idx+1} ({duration_text})",
                        "content": section_summary,
                        "time_point": start_time,
                        "end_time": end_time,
                        "keyframe_count": len(section["keyframes"])
                    })
                
                # 保存摘要到数据库
                video_summary = VideoSummary(
                    video_id=video_id,
                    whole_summary=summary_data['summary'],  # 使用whole_summary字段保存整体摘要
                    generate_time=datetime.now()
                )
                from models.models import Keyword,VideoKeyword,CourseKeyword                # 批量处理关键词以提高性能
                if summary_data['keywords']:
                    # 一次性查询所有可能存在的关键词
                    existing_keywords = {kw.name: kw for kw in Keyword.query.filter(Keyword.name.in_(summary_data['keywords'])).all()}
                    
                    # 准备批量插入的数据
                    new_keywords = []
                    all_keyword_objects = []
                    
                    for keyword_name in summary_data['keywords']:
                        # 获取或创建关键词
                        if keyword_name in existing_keywords:
                            keyword_obj = existing_keywords[keyword_name]
                            add_task_log(task_id, video_id, 'debug', f"使用已存在的关键词: {keyword_name} (ID: {keyword_obj.id})")
                        else:
                            keyword_obj = Keyword(name=keyword_name, category='specific_point')
                            new_keywords.append(keyword_obj)
                            existing_keywords[keyword_name] = keyword_obj
                            add_task_log(task_id, video_id, 'debug', f"创建新关键词: {keyword_name}")
                        
                        all_keyword_objects.append(keyword_obj)
                    
                    add_task_log(task_id, video_id, 'debug', f"准备插入 {len(new_keywords)} 个新关键词")
                    
                    # 批量添加新关键词并确保获得ID
                    if new_keywords:
                        db.session.add_all(new_keywords)
                        db.session.flush()  # 确保获得ID
                        add_task_log(task_id, video_id, 'debug', f"新关键词已插入数据库，获得ID: {[kw.id for kw in new_keywords]}")
                    
                    # 现在所有关键词都有ID了，创建关系
                    video_keywords = []
                    course_keywords_to_check = []
                    
                    for keyword_obj in all_keyword_objects:
                        # 现在keyword_obj.id一定有值
                        video_keywords.append(VideoKeyword(video_id=video_id, keyword_id=keyword_obj.id))
                        course_keywords_to_check.append(keyword_obj.id)
                        add_task_log(task_id, video_id, 'debug', f"准备关联关键词 {keyword_obj.name} (ID: {keyword_obj.id}) 到视频 {video_id}")
                    
                    add_task_log(task_id, video_id, 'debug', f"准备插入 {len(video_keywords)} 个视频关键词关系")
                    
                    # 批量添加视频关键词关系
                    db.session.add_all(video_keywords)
                    
                    # 批量检查和添加课程关键词关系
                    existing_course_keywords = {ck.keyword_id for ck in CourseKeyword.query.filter(
                        CourseKeyword.course_id == video.course_id,
                        CourseKeyword.keyword_id.in_(course_keywords_to_check)
                    ).all()}
                    
                    add_task_log(task_id, video_id, 'debug', f"课程 {video.course_id} 已有关键词ID: {existing_course_keywords}")
                    
                    new_course_keywords = []
                    for keyword_id in course_keywords_to_check:
                        if keyword_id not in existing_course_keywords:
                            new_course_keywords.append(CourseKeyword(course_id=video.course_id, keyword_id=keyword_id))
                            add_task_log(task_id, video_id, 'debug', f"准备关联关键词ID {keyword_id} 到课程 {video.course_id}")
                    
                    add_task_log(task_id, video_id, 'debug', f"准备插入 {len(new_course_keywords)} 个新的课程关键词关系")
                    
                    if new_course_keywords:
                        db.session.add_all(new_course_keywords)
                
                # 使用区间摘要作为sections
                video_summary.set_sections(section_summaries)
                
                db.session.add(video_summary)
                db.session.commit()
                add_task_log(task_id, video_id, 'info', f"视频摘要生成成功: {len(summary_data['keywords'])}个关键词")
            else:
                add_task_log(task_id, video_id, 'warning', "视频摘要生成失败")
        
        # 10. 更新任务状态为完成
        task.status = "completed"
        task.progress = 1.0
        task.end_time = datetime.now()
        db.session.commit()
        
        add_task_log(task_id, video_id, 'info', f"视频处理完成, 总用时: {(task.end_time - task.start_time).total_seconds()} 秒")
        
        return True
    except Exception as e:
        # 更新任务状态为失败
        db.session.rollback()
        task = VideoProcessingTask.query.filter_by(video_id=video_id).first()
        if task:
            task.status = "failed"
            task.error_message = str(e)
            task.end_time = datetime.now()
            db.session.commit()
            add_task_log(task.task_id, video_id, 'error', f"处理视频任务失败: {str(e)}")
        
        current_app.logger.error(f"处理视频任务失败: {str(e)}")
        return False
