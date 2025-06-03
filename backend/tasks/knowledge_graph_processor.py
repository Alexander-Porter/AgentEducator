"""
知识图谱处理器
负责从视频关键词生成课程知识图谱
"""

import json
import re
from datetime import datetime
from flask import current_app
from openai import OpenAI
from sqlalchemy import func
from collections import defaultdict, Counter

from tqdm import tqdm

from models.models import (
    db, Video, Course, 
    Keyword, VideoKeyword, CourseKeyword, 
    KeywordRelation, KnowledgeGraphProcessingTask
)

class KnowledgeGraphProcessor:
    """知识图谱处理器"""
    
    def __init__(self, api_key=None, base_url=None):
        """初始化处理器"""
        import os
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.base_url = base_url or os.environ.get("SILICON_API_BASE", "https://api.siliconflow.cn/v1")
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
    
    def check_videos_processed_status(self, course_id):
        """
        检测课程中哪些视频已经被知识图谱处理过
        
        通过检查视频的关键词是否参与了 KeywordRelation 来判断
        如果视频的关键词存在于 KeywordRelation 中，说明该视频已被处理
        
        Args:
            course_id: 课程ID
            
        Returns:
            dict: {
                'processed_videos': [video_id1, video_id2, ...],  # 已处理的视频ID列表
                'unprocessed_videos': [video_id3, video_id4, ...],  # 未处理的视频ID列表
                'total_videos': int,  # 总视频数
                'processed_count': int,  # 已处理数
                'unprocessed_count': int  # 未处理数
            }
        """
        try:
            # 获取课程下所有视频
            videos = db.session.query(Video).join(Course).filter(
                Course.id == course_id,
                Video.is_deleted == False
            ).all()
            
            if not videos:
                return {
                    'processed_videos': [],
                    'unprocessed_videos': [],
                    'total_videos': 0,
                    'processed_count': 0,
                    'unprocessed_count': 0
                }
            
            processed_videos = []
            unprocessed_videos = []
            
            for video in videos:
                # 检查视频是否已被知识图谱处理
                is_processed = self._is_video_processed_by_knowledge_graph(video.id)
                
                if is_processed:
                    processed_videos.append(str(video.id))
                else:
                    unprocessed_videos.append(str(video.id))
            
            result = {
                'processed_videos': processed_videos,
                'unprocessed_videos': unprocessed_videos,
                'total_videos': len(videos),
                'processed_count': len(processed_videos),
                'unprocessed_count': len(unprocessed_videos)
            }
            
            current_app.logger.info(f"课程 {course_id} 视频处理状态检查完成: "
                                  f"总共{result['total_videos']}个视频，"
                                  f"已处理{result['processed_count']}个，"
                                  f"未处理{result['unprocessed_count']}个")
            
            return result
            
        except Exception as e:
            current_app.logger.error(f"检查视频处理状态失败: {str(e)}")
            raise
    
    def _is_video_processed_by_knowledge_graph(self, video_id):
        """
        检查单个视频是否已被知识图谱处理过
        
        检查逻辑：
        1. 视频必须有VideoKeyword关系（有关键词提取）
        2. 视频的关键词必须参与了KeywordRelation（知识图谱关系建立）
        
        Args:
            video_id: 视频ID
            
        Returns:
            bool: True表示已处理，False表示未处理
        """
        try:
            # 获取视频的关键词
            video_keywords = db.session.query(VideoKeyword).filter(
                VideoKeyword.video_id == video_id
            ).all()
            
            if not video_keywords:
                # 没有关键词提取，肯定未处理
                return False
            
            # 获取视频关键词的ID列表
            keyword_ids = [vk.keyword_id for vk in video_keywords]
            
            # 检查是否有任何关键词参与了KeywordRelation
            relation_count = db.session.query(KeywordRelation).filter(
                db.or_(
                    KeywordRelation.source_keyword_id.in_(keyword_ids),
                    KeywordRelation.target_keyword_id.in_(keyword_ids)
                )
            ).count()
            
            # 如果有关键词参与了关系建立，说明已被知识图谱处理
            return relation_count > 0
            
        except Exception as e:
            current_app.logger.error(f"检查视频 {video_id} 处理状态失败: {str(e)}")
            return False

    def process_course_knowledge_graph_incremental(self, course_id, stop_flag=None):
        """
        增量处理课程知识图谱生成
        
        只处理未被知识图谱处理过的新视频，提高处理效率
        
        Args:
            course_id: 课程ID
            stop_flag: 停止标志
            
        Returns:
            tuple: (success, result)
        """
        try:
            # 检查视频处理状态
            video_status = self.check_videos_processed_status(course_id)
            
            if video_status['unprocessed_count'] == 0:
                current_app.logger.info(f"课程 {course_id} 的所有视频都已被知识图谱处理，无需增量更新")
                return True, {
                    'message': '所有视频都已处理，无需增量更新',
                    'video_status': video_status,
                    'keywords_count': 0,
                    'relations_count': 0
                }
            
            # 创建任务记录
            task = KnowledgeGraphProcessingTask(
                course_id=course_id,
                task_type='incremental_knowledge_graph',
                status='processing',
                start_time=datetime.now()
            )
            db.session.add(task)
            db.session.commit()
            
            current_app.logger.info(f"开始增量处理课程 {course_id} 的知识图谱，"
                                  f"需要处理 {video_status['unprocessed_count']} 个新视频")
            
            # 检查是否请求停止
            if stop_flag and stop_flag.is_set():
                task.status = 'cancelled'
                task.error_message = '任务被手动停止'
                task.end_time = datetime.now()
                db.session.commit()
                return False, '任务被手动停止'
            
            # 1. 增量提取和分类关键词（只处理新视频）
            task.progress = 0.1
            db.session.commit()
            keywords_data = self._extract_and_categorize_keywords_incremental(
                course_id, video_status['unprocessed_videos']
            )
            
            # 检查是否请求停止
            if stop_flag and stop_flag.is_set():
                task.status = 'cancelled'
                task.error_message = '任务被手动停止'
                task.end_time = datetime.now()
                db.session.commit()
                return False, '任务被手动停止'
            
            # 2. 增量建立关键词关系（包含新旧关键词的关系）
            task.progress = 0.6
            db.session.commit()
            relations_data = self._build_keyword_relations_incremental(course_id, keywords_data, task)
            
            # 检查是否请求停止
            if stop_flag and stop_flag.is_set():
                task.status = 'cancelled'
                task.error_message = '任务被手动停止'
                task.end_time = datetime.now()
                db.session.commit()
                return False, '任务被手动停止'
            
            # 3. 更新课程级别关键词统计
            task.progress = 0.9
            db.session.commit()
            self._update_course_keyword_stats(course_id)
            
            # 4. 完成任务
            task.status = 'completed'
            task.progress = 1.0
            task.end_time = datetime.now()
            task.set_result_data({
                'keywords_count': len(keywords_data),
                'relations_count': len(relations_data),
                'video_status': video_status,
                'message': f'增量知识图谱生成成功，处理了{video_status["unprocessed_count"]}个新视频'
            })
            db.session.commit()
            
            current_app.logger.info(f"课程 {course_id} 增量知识图谱生成完成")
            return True, task.to_dict()
            
        except Exception as e:
            # 更新任务状态为失败
            if 'task' in locals():
                task.status = 'failed'
                task.error_message = str(e)
                task.end_time = datetime.now()
                db.session.commit()
            
            current_app.logger.error(f"增量知识图谱生成失败: {str(e)}")
            return False, str(e)

    def _extract_and_categorize_keywords_incremental(self, course_id, unprocessed_video_ids):
        """
        增量提取和分类关键词
        
        只处理未被知识图谱处理过的视频关键词
        
        Args:
            course_id: 课程ID
            unprocessed_video_ids: 未处理的视频ID列表
            
        Returns:
            dict: 分类后的关键词字典
        """
        if not unprocessed_video_ids:
            current_app.logger.info("没有未处理的视频，跳过关键词提取")
            return {"core_concept": [], "main_module": [], "specific_point": []}
        
        # 获取未处理视频的关键词
        videos = db.session.query(Video).filter(
            Video.id.in_(unprocessed_video_ids),
            Video.is_deleted == False
        ).all()
        
        if not videos:
            current_app.logger.warning(f"未找到指定的未处理视频")
            return {"core_concept": [], "main_module": [], "specific_point": []}
        
        # 收集新视频的关键词
        new_keywords = []
        video_keyword_map = {}
        
        for video in videos:
            video_keywords = db.session.query(VideoKeyword).filter(
                VideoKeyword.video_id == video.id
            ).all()
            
            if not video_keywords:
                current_app.logger.warning(f"视频 {video.id} 没有关键词，跳过")
                continue
            
            # 收集关键词
            video_keywords_list = [vk.keyword.name for vk in video_keywords]
            new_keywords.extend(video_keywords_list)
            video_keyword_map[video.id] = video_keywords_list
            
            current_app.logger.info(f"新视频 {video.id} 收集到 {len(video_keywords_list)} 个关键词")
        
        # 统计关键词频率
        keyword_counter = Counter(new_keywords)
        unique_new_keywords = list(keyword_counter.keys())
        
        current_app.logger.info(f"课程 {course_id} 从新视频中收集到 {len(unique_new_keywords)} 个唯一关键词")
        
        if not unique_new_keywords:
            return {"core_concept": [], "main_module": [], "specific_point": []}
        
        # 使用LLM对新关键词进行分类
        categorized_keywords = self._categorize_keywords_with_llm(unique_new_keywords, course_id)
        
        # 保存关键词分类到数据库
        self._save_keywords_to_db(categorized_keywords, video_keyword_map, course_id, keyword_counter)
        
        return categorized_keywords

    def _build_keyword_relations_incremental(self, course_id, new_categorized_keywords, task=None):
        """
        增量建立关键词关系
        
        结合新关键词和已有关键词，建立完整的关系网络
        
        Args:
            course_id: 课程ID
            new_categorized_keywords: 新分类的关键词
            task: 任务对象
            
        Returns:
            list: 新建立的关系列表
        """
        # 获取课程所有关键词（包括新旧）
        all_course_keywords = db.session.query(Keyword).join(VideoKeyword).join(Video).join(Course).filter(
            Course.id == course_id
        ).distinct().all()
        
        if len(all_course_keywords) < 2:
            current_app.logger.warning("关键词数量不足，无法建立关系")
            return []
        
        # 检查是否有新关键词
        new_keywords = []
        for category_keywords in new_categorized_keywords.values():
            new_keywords.extend(category_keywords)
        
        if not new_keywords:
            current_app.logger.info("没有新关键词，跳过关系建立")
            return []
        
        current_app.logger.info(f"增量关系建立：总关键词{len(all_course_keywords)}个，新关键词{len(new_keywords)}个")
        
        # 使用LLM分析关键词关系（重点分析新关键词与已有关键词的关系）
        relations = self._analyze_keyword_relations_with_llm_incremental(
            all_course_keywords, new_keywords, task
        )
        
        # 保存关系到数据库
        self._save_relations_to_db(relations)
        
        return relations

    def _analyze_keyword_relations_with_llm_incremental(self, all_keywords, new_keywords, task=None):
        """
        增量分析关键词关系
        
        重点分析新关键词与已有关键词之间的关系，避免重复分析已存在的关系
        
        Args:
            all_keywords: 课程所有关键词对象列表
            new_keywords: 新关键词名称列表
            task: 任务对象
            
        Returns:
            list: 新关系列表
        """
        keyword_dict = {kw.name: kw for kw in all_keywords}
        new_keyword_set = set(new_keywords)
        existing_keywords = [kw.name for kw in all_keywords if kw.name not in new_keyword_set]
        
        current_app.logger.info(f"增量关系分析：新关键词{len(new_keywords)}个，已有关键词{len(existing_keywords)}个")
        
        # 系统提示词（专门针对增量分析）
        system_prompt = """
你是一个专业的教育知识图谱分析AI助手。现在需要你分析新关键词与已有关键词之间的关系。

关系类型定义：
1. prerequisite: A是B的前置知识（A -> B，学习B需要先掌握A）
2. related: A和B相关但没有明确的前后顺序
3. contains: A包含B（A是更大的概念，B是A的一部分）

重点关注以下关系：
- 新关键词与已有关键词之间的关系
- 新关键词之间的关系
- 避免分析已有关键词之间的关系（已存在）

返回JSON格式：
{
  "relations": [
    {
      "source": "关键词A",
      "target": "关键词B", 
      "type": "prerequisite",
      "strength": 0.8,
      "description": "关系描述"
    }
  ]
}

注意：
- strength范围0-1，表示关系强度
- 每个关系要有简短的描述说明
- 只返回涉及新关键词的关系
"""
        
        all_relations = []
        
        # 策略1: 分析新关键词与已有关键词的关系
        if existing_keywords and new_keywords:
            current_app.logger.info("分析新关键词与已有关键词的关系...")
            
            # 分批处理，避免上下文过长
            batch_size = 20
            new_keyword_batches = [new_keywords[i:i + batch_size] for i in range(0, len(new_keywords), batch_size)]
            
            for i, new_batch in enumerate(new_keyword_batches):
                if task:
                    progress = 0.6 + (i / len(new_keyword_batches)) * 0.15
                    task.progress = progress
                    db.session.commit()
                
                # 选择最相关的已有关键词进行分析（限制数量避免上下文过长）
                relevant_existing = existing_keywords[:30] if len(existing_keywords) > 30 else existing_keywords
                
                combined_keywords = relevant_existing + new_batch
                keywords_text = ", ".join(combined_keywords)
                
                analysis_prompt = system_prompt + f"""

当前分析场景：新关键词与已有关键词的关系分析
已有关键词（前{len(relevant_existing)}个）：{', '.join(relevant_existing)}
新关键词：{', '.join(new_batch)}

请重点分析新关键词与已有关键词之间的关系。
"""
                
                relations = self._call_llm_for_relations(analysis_prompt, keywords_text, f"新关键词批次{i+1}与已有关键词")
                all_relations.extend(relations)
        
        # 策略2: 分析新关键词之间的关系
        if len(new_keywords) > 1:
            current_app.logger.info("分析新关键词之间的关系...")
            
            if task:
                task.progress = 0.75
                db.session.commit()
            
            keywords_text = ", ".join(new_keywords)
            
            new_relations_prompt = system_prompt + f"""

当前分析场景：新关键词之间的关系分析
新关键词：{', '.join(new_keywords)}

请分析这些新关键词之间的关系。
"""
            
            relations = self._call_llm_for_relations(new_relations_prompt, keywords_text, "新关键词之间")
            all_relations.extend(relations)
        
        # 验证和过滤关系
        valid_relations = []
        seen_relations = set()
        
        for relation in all_relations:
            source_name = relation.get('source')
            target_name = relation.get('target')
            relation_type = relation.get('type')
            
            # 确保关键词存在
            if (source_name in keyword_dict and target_name in keyword_dict and 
                source_name != target_name):
                
                # 确保至少有一个是新关键词
                if source_name in new_keyword_set or target_name in new_keyword_set:
                    relation_key = (source_name, target_name, relation_type)
                    reverse_key = (target_name, source_name, relation_type)
                    
                    # 避免重复关系
                    if relation_key not in seen_relations:
                        if relation_type == 'related' and reverse_key in seen_relations:
                            continue
                        
                        # 检查数据库中是否已存在该关系
                        existing_relation = KeywordRelation.query.filter_by(
                            source_keyword_id=keyword_dict[source_name].id,
                            target_keyword_id=keyword_dict[target_name].id,
                            relation_type=relation_type
                        ).first()
                        
                        if not existing_relation:
                            relation['source_keyword'] = keyword_dict[source_name]
                            relation['target_keyword'] = keyword_dict[target_name]
                            valid_relations.append(relation)
                            seen_relations.add(relation_key)
        
        current_app.logger.info(f"增量关键词关系分析完成，发现 {len(valid_relations)} 个新关系")
        return valid_relations

    def _call_llm_for_relations(self, system_prompt, keywords_text, description):
        """调用LLM分析关系的通用方法"""
        try:
            response = self.client.chat.completions.create(
                model="THUDM/GLM-Z1-9B-0414",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"请分析以下关键词之间的关系：\n{keywords_text}"}
                ],
                temperature=0.1,
                max_tokens=8192
            )
            
            result_text = response.choices[0].message.content
            
            # 解析JSON结果
            try:
                batch_result = json.loads(result_text)
                if 'relations' in batch_result:
                    current_app.logger.info(f"{description}分析完成，发现{len(batch_result['relations'])}个关系")
                    return batch_result['relations']
            except json.JSONDecodeError:
                # 尝试提取JSON部分
                json_pattern = r'(\{[\s\S]*\})'
                match = re.search(json_pattern, result_text)
                if match:
                    try:
                        batch_result = json.loads(match.group(1))
                        if 'relations' in batch_result:
                            current_app.logger.info(f"{description}分析完成，发现{len(batch_result['relations'])}个关系")
                            return batch_result['relations']
                    except:
                        current_app.logger.warning(f"无法解析{description}的关系结果: {result_text}")
                else:
                    current_app.logger.warning(f"无法找到{description}的JSON格式结果: {result_text}")
        except Exception as e:
            current_app.logger.error(f"{description}关系分析失败: {str(e)}")
        
        return []

    def process_course_knowledge_graph(self, course_id, force_regenerate=False, stop_flag=None, incremental=True):
        """
        处理课程知识图谱生成
        
        Args:
            course_id: 课程ID
            force_regenerate: 是否强制重新生成（忽略增量检测）
            stop_flag: 停止标志
            incremental: 是否使用增量处理（默认为True）
        """
        # 如果不强制重新生成且启用增量处理，先尝试增量处理
        if not force_regenerate and incremental:
            # 检查是否可以进行增量处理
            video_status = self.check_videos_processed_status(course_id)
            
            if video_status['unprocessed_count'] > 0:
                current_app.logger.info(f"检测到 {video_status['unprocessed_count']} 个未处理视频，使用增量处理模式")
                return self.process_course_knowledge_graph_incremental(course_id, stop_flag)
            elif video_status['total_videos'] == 0:
                current_app.logger.warning(f"课程 {course_id} 没有视频，无法生成知识图谱")
                return False, "课程没有视频，无法生成知识图谱"
            else:
                current_app.logger.info(f"课程 {course_id} 所有视频都已处理，知识图谱是最新的")
                return True, {
                    'message': '知识图谱已是最新，无需重新生成',
                    'video_status': video_status,
                    'is_up_to_date': True
                }
        
        # 执行完整的知识图谱生成
        return self._process_course_knowledge_graph_full(course_id, force_regenerate, stop_flag)
    
    def _process_course_knowledge_graph_full(self, course_id, force_regenerate=False, stop_flag=None):
        """执行完整的知识图谱生成（原有逻辑）"""
        try:
            # 查找或创建任务记录
            task = KnowledgeGraphProcessingTask.query.filter_by(
                course_id=course_id, 
                status='pending'
            ).first()
            
            if task:
                task.status = 'processing'
                task.start_time = datetime.now()
            else:
                # 创建新任务记录
                task = KnowledgeGraphProcessingTask(
                    course_id=course_id,
                    task_type='full_knowledge_graph',
                    status='processing',
                    start_time=datetime.now()
                )
                db.session.add(task)
            
            db.session.commit()
            
            current_app.logger.info(f"开始完整处理课程 {course_id} 的知识图谱生成")
            
            # 检查是否请求停止
            if stop_flag and stop_flag.is_set():
                task.status = 'cancelled'
                task.error_message = '任务被手动停止'
                task.end_time = datetime.now()
                db.session.commit()
                return False, '任务被手动停止'
            
            # 1. 提取和分类关键词
            task.progress = 0.1
            db.session.commit()
            keywords_data = self._extract_and_categorize_keywords(course_id, force_regenerate)
            
            # 检查是否请求停止
            if stop_flag and stop_flag.is_set():
                task.status = 'cancelled'
                task.error_message = '任务被手动停止'
                task.end_time = datetime.now()
                db.session.commit()
                return False, '任务被手动停止'
              # 2. 建立关键词关系
            task.progress = 0.6
            db.session.commit()
            relations_data = self._build_keyword_relations(course_id, keywords_data, task)
            
            # 检查是否请求停止
            if stop_flag and stop_flag.is_set():
                task.status = 'cancelled'
                task.error_message = '任务被手动停止'
                task.end_time = datetime.now()
                db.session.commit()
                return False, '任务被手动停止'
            
            # 3. 更新课程级别关键词统计
            task.progress = 0.9
            db.session.commit()
            self._update_course_keyword_stats(course_id)
            
            # 4. 完成任务
            task.status = 'completed'
            task.progress = 1.0
            task.end_time = datetime.now()
            task.set_result_data({
                'keywords_count': len(keywords_data),
                'relations_count': len(relations_data),
                'message': '完整知识图谱生成成功'
            })
            db.session.commit()
            
            current_app.logger.info(f"课程 {course_id} 完整知识图谱生成完成")
            return True, task.to_dict()
            
        except Exception as e:
            # 更新任务状态为失败
            if 'task' in locals():
                task.status = 'failed'
                task.error_message = str(e)
                task.end_time = datetime.now()
                db.session.commit()
            
            current_app.logger.error(f"完整知识图谱生成失败: {str(e)}")
            return False, str(e)
    
    def _extract_and_categorize_keywords(self, course_id, force_regenerate=False):
        """提取和分类关键词"""
        # 获取课程下所有视频的关键词
        videos = db.session.query(Video).join(Course).filter(
            Course.id == course_id,
            Video.is_deleted == False
        ).all()
        
        if not videos:
            current_app.logger.warning(f"课程 {course_id} 下没有找到视频")
            return []
        
        # 收集所有视频的关键词
        all_keywords = []
        video_keyword_map = {}
        
        #改为用VideoKeyword表查询
        for video in videos:
            video_keywords = db.session.query(VideoKeyword).filter(
                VideoKeyword.video_id == video.id
            ).all()
            
            if not video_keywords:
                current_app.logger.warning(f"视频 {video.id} 没有关键词")
                continue
            
            # 收集关键词
            video_keywords_list = [vk.keyword.name for vk in video_keywords]
            all_keywords.extend(video_keywords_list)
            video_keyword_map[video.id] = video_keywords_list
            
            current_app.logger.info(f"视频 {video.id} 收集到 {len(video_keywords_list)} 个关键词")
        
        # 统计关键词频率
        keyword_counter = Counter(all_keywords)
        unique_keywords = list(keyword_counter.keys())
        
        current_app.logger.info(f"课程 {course_id} 收集到 {len(unique_keywords)} 个唯一关键词")
        
        # 使用LLM对关键词进行分类
        categorized_keywords = self._categorize_keywords_with_llm(unique_keywords, course_id)
        
        # 保存关键词到数据库
        self._save_keywords_to_db(categorized_keywords, video_keyword_map, course_id, keyword_counter)
        
        return categorized_keywords
    
    def _categorize_keywords_with_llm(self, keywords, course_id):
        """使用LLM对关键词进行分类"""
        # 获取课程信息
        course = Course.query.get(course_id)
        course_name = course.name if course else "未知课程"
        
        # 构建分类提示词
        system_prompt = f"""
你是一个专业的教育内容分析AI助手。现在需要你对"{course_name}"课程的关键词进行分类。

请将关键词分为三个类别，从宽泛到具体：
1. core_concept (核心概念): 课程的核心理论概念和基础知识点
2. main_module (主要模块): 课程的主要章节、模块或知识领域  
3. specific_point (具体知识点): 具体的技术点、方法、工具或细节知识
以计算机网络课程为例，关键词可能包括：
1.核心概念: 网络层，应用层，传输层
2.主要模块: IPV4协议，TCP协议，网络安全
3.具体知识点: "TCP三次握手", "IP地址分配", "防火墙配置", "数据报格式"

分类原则：
- 核心概念：基础性、理论性强的概念，是理解其他知识的基础
- 主要模块：较大的知识模块，通常包含多个具体知识点
- 具体知识点：具体的实现方法、技术细节、工具使用等

请按照以下JSON格式返回结果：
{{
  "core_concept": ["关键词1", "关键词2", ...],
  "main_module": ["关键词1", "关键词2", ...], 
  "specific_point": ["关键词1", "关键词2", ...]
}}

确保所有输入的关键词都被分类，不要遗漏任何关键词。
"""
        
        # 分批处理关键词（避免上下文过长）
        batch_size = 50
        all_categorized = {"core_concept": [], "main_module": [], "specific_point": []}
        
        current_app.logger.info(f"开始对课程 {course_name} 的关键词进行分类，共 {len(keywords)} 个关键词")
        
        # 使用tqdm显示进度
        batches = [keywords[i:i + batch_size] for i in range(0, len(keywords), batch_size)]
        for batch_keywords in tqdm(batches, desc="分类关键词", unit="batch"):
            keywords_text = ", ".join(batch_keywords)
            
            try:
                response = self.client.chat.completions.create(
                    model="THUDM/GLM-Z1-9B-0414",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"请对以下关键词进行分类：\n{keywords_text}"}
                    ],
                    temperature=0.1,
                    max_tokens=8192
                )
                
                result_text = response.choices[0].message.content
                
                # 解析JSON结果
                try:
                    batch_result = json.loads(result_text)
                    for category, kws in batch_result.items():
                        if category in all_categorized:
                            all_categorized[category].extend(kws)
                except json.JSONDecodeError:
                    # 如果解析失败，尝试提取JSON部分
                    json_pattern = r'(\{[\s\S]*\})'
                    match = re.search(json_pattern, result_text)
                    if match:
                        try:
                            batch_result = json.loads(match.group(1))
                            for category, kws in batch_result.items():
                                if category in all_categorized:
                                    all_categorized[category].extend(kws)
                        except:
                            current_app.logger.warning(f"无法解析关键词分类结果: {result_text}")
                            # 默认分类为具体知识点
                            all_categorized["specific_point"].extend(batch_keywords)
                    else:
                        current_app.logger.warning(f"无法找到JSON格式的分类结果: {result_text}")
                        all_categorized["specific_point"].extend(batch_keywords)
                        
            except Exception as e:
                current_app.logger.error(f"关键词分类失败: {str(e)}")
                # 默认分类为具体知识点
                all_categorized["specific_point"].extend(batch_keywords)
        
        # 验证所有关键词都被分类
        categorized_count = sum(len(kws) for kws in all_categorized.values())
        if categorized_count != len(keywords):
            current_app.logger.warning(f"关键词分类不完整，输入{len(keywords)}个，分类{categorized_count}个")
        
        current_app.logger.info(f"关键词分类完成: 核心概念{len(all_categorized['core_concept'])}个, "
                              f"主要模块{len(all_categorized['main_module'])}个, "
                              f"具体知识点{len(all_categorized['specific_point'])}个")
        
        return all_categorized
    def _save_keywords_to_db(self, categorized_keywords, video_keyword_map, course_id, keyword_counter):
        """更新关键词分类到数据库（VideoKeyword关系已存在，只需更新Keyword的category）"""
        updated_keywords = []
        
        # 更新每个分类的关键词
        for category, keywords in categorized_keywords.items():
            for keyword_name in keywords:
                # 查找已存在的关键词
                existing_keyword = Keyword.query.filter_by(name=keyword_name).first()
                if existing_keyword:
                    # 更新关键词分类，如果与当前分类不同
                    if existing_keyword.category != category:
                        current_app.logger.info(f"更新关键词 '{keyword_name}' 分类: {existing_keyword.category} -> {category}")
                        existing_keyword.category = category
                        existing_keyword.description = f"来自课程的{category}关键词"
                        existing_keyword.update_time = datetime.now()
                        updated_keywords.append(existing_keyword)
                else:
                    # 如果关键词不存在，创建新的（这种情况理论上不应该发生，因为我们是从VideoKeyword获取的）
                    continue
                    current_app.logger.warning(f"关键词 '{keyword_name}' 在数据库中不存在，创建新记录")
                    new_keyword = Keyword(
                        name=keyword_name,
                        category=category,
                        description=f"来自课程的{category}关键词"
                    )
                    db.session.add(new_keyword)
                    updated_keywords.append(new_keyword)
        
        # 批量提交更新
        if updated_keywords:
            db.session.commit()
            current_app.logger.info(f"关键词分类更新完成，共更新 {len(updated_keywords)} 个关键词")
        else:
            current_app.logger.info("所有关键词分类都是最新的，无需更新")
    
    def _build_keyword_relations(self, course_id, categorized_keywords, task=None):
        """建立关键词之间的关系"""
        # 获取课程所有关键词
        course_keywords = db.session.query(Keyword).join(VideoKeyword).join(Video).join(Course).filter(
            Course.id == course_id
        ).distinct().all()
        
        if len(course_keywords) < 2:
            current_app.logger.warning("关键词数量不足，无法建立关系")
            return []
        
        # 使用LLM分析关键词关系
        relations = self._analyze_keyword_relations_with_llm(course_keywords, task)
          # 保存关系到数据库
        self._save_relations_to_db(relations)
        
        return relations
    
    def _analyze_keyword_relations_with_llm(self, keywords, task=None):
        """使用LLM分析关键词关系 - 优先建立跨级别关系"""
        keyword_dict = {kw.name: kw for kw in keywords}
        
        # 按分类分组关键词
        categorized_keywords = {
            'core_concept': [],
            'main_module': [],
            'specific_point': []
        }
        
        for keyword in keywords:
            category = getattr(keyword, 'category', 'specific_point')
            if category in categorized_keywords:
                categorized_keywords[category].append(keyword.name)
            else:
                categorized_keywords['specific_point'].append(keyword.name)
        
        current_app.logger.info(f"关键词分类统计: 核心概念{len(categorized_keywords['core_concept'])}个, "
                              f"主要模块{len(categorized_keywords['main_module'])}个, "
                              f"具体知识点{len(categorized_keywords['specific_point'])}个")
        
        system_prompt = """
你是一个专业的教育知识图谱分析AI助手。现在需要你分析关键词之间的关系。

关系类型定义：
1. prerequisite: A是B的前置知识（A -> B，学习B需要先掌握A）
2. related: A和B相关但没有明确的前后顺序
3. contains: A包含B（A是更大的概念，B是A的一部分）

请分析给定关键词之间的关系，返回有意义的关系对。特别关注：
- 核心概念包含主要模块的关系（contains）
- 主要模块包含具体知识点的关系（contains）
- 核心概念作为主要模块前置知识的关系（prerequisite）
- 主要模块作为具体知识点前置知识的关系（prerequisite）

返回JSON格式：
{{
  "relations": [
    {{
      "source": "关键词A",
      "target": "关键词B", 
      "type": "prerequisite",
      "strength": 0.8,
      "description": "关系描述"
    }},
    ...
  ]
}}

注意：
- strength范围0-1，表示关系强度
- 优先返回跨层级的包含关系(contains)和前置关系(prerequisite)
- 每个关系要有简短的描述说明
"""
        all_relations = []
        total_steps = 0
        current_step = 0
        
        # 计算总的分析步骤数用于进度跟踪
        if categorized_keywords['core_concept']:
            if categorized_keywords['main_module']:
                total_steps += 1  # 核心概念与主要模块
            if categorized_keywords['specific_point']:
                specific_batches = self._create_batches(categorized_keywords['specific_point'], 15)
                total_steps += len(specific_batches)  # 核心概念与具体知识点各批次
        
        if categorized_keywords['main_module'] and categorized_keywords['specific_point']:
            specific_batches = self._create_batches(categorized_keywords['specific_point'], 12)
            total_steps += len(specific_batches)  # 主要模块与具体知识点各批次
            
        # 同级别关系分析步骤
        if len(categorized_keywords['core_concept']) > 1:
            total_steps += 1
        if len(categorized_keywords['main_module']) > 1:
            total_steps += 1
        if len(categorized_keywords['specific_point']) > 1:
            total_steps += 1
        
        # 策略1: 优先分析核心概念与所有其他关键词的关系
        if categorized_keywords['core_concept']:
            current_app.logger.info("优先分析核心概念与其他关键词的跨级别关系...")
            
            # 核心概念与主要模块的关系
            if categorized_keywords['main_module']:
                current_step += 1
                if task:
                    task.progress = 0.6 + (current_step / total_steps) * 0.25
                    db.session.commit()
                    
                relations = self._analyze_cross_level_relations(
                    categorized_keywords['core_concept'], 
                    categorized_keywords['main_module'], 
                    system_prompt,
                    "核心概念与主要模块"
                )
                all_relations.extend(relations)
              # 核心概念与具体知识点的关系（分批处理）
            if categorized_keywords['specific_point']:
                specific_batches = self._create_batches(categorized_keywords['specific_point'], 15)
                # 使用tqdm显示进度
                for i, batch in enumerate(tqdm(specific_batches, desc="核心概念与具体知识点关系分析", unit="批次")):
                    current_step += 1
                    if task:
                        task.progress = 0.6 + (current_step / total_steps) * 0.25
                        db.session.commit()
                        
                    relations = self._analyze_cross_level_relations(
                        categorized_keywords['core_concept'], 
                        batch, 
                        system_prompt,
                        f"核心概念与具体知识点批次{i+1}"
                    )
                    all_relations.extend(relations)
          # 策略2: 分析主要模块与具体知识点的关系
        if categorized_keywords['main_module'] and categorized_keywords['specific_point']:
            current_app.logger.info("分析主要模块与具体知识点的跨级别关系...")
            
            specific_batches = self._create_batches(categorized_keywords['specific_point'], 12)
            # 使用tqdm显示进度
            for i, batch in enumerate(tqdm(specific_batches, desc="主要模块与具体知识点关系分析", unit="批次")):
                current_step += 1
                if task:
                    task.progress = 0.6 + (current_step / total_steps) * 0.25
                    db.session.commit()
                    
                relations = self._analyze_cross_level_relations(
                    categorized_keywords['main_module'], 
                    batch, 
                    system_prompt,
                    f"主要模块与具体知识点批次{i+1}"
                )
                all_relations.extend(relations)
        
        # 策略3: 同级别内部关系分析（使用滑动窗口避免遗漏）
        current_app.logger.info("分析同级别内部关系...")
        
        # 创建同级别分析任务列表用于tqdm进度显示
        same_level_tasks = []
        if len(categorized_keywords['core_concept']) > 1:
            same_level_tasks.append(('core_concept', '核心概念内部'))
        if len(categorized_keywords['main_module']) > 1:
            same_level_tasks.append(('main_module', '主要模块内部'))
        if len(categorized_keywords['specific_point']) > 1:
            same_level_tasks.append(('specific_point', '具体知识点内部'))
        
        # 使用tqdm显示同级别关系分析进度
        for category, description in tqdm(same_level_tasks, desc="同级别关系分析", unit="类别"):
            current_step += 1
            if task:
                task.progress = 0.6 + (current_step / total_steps) * 0.25
                db.session.commit()
            
            if category == 'specific_point':
                # 具体知识点使用滑动窗口分析
                relations = self._analyze_specific_points_relations(
                    categorized_keywords[category], 
                    system_prompt
                )
            else:
                # 核心概念和主要模块直接分析
                relations = self._analyze_same_level_relations(
                    categorized_keywords[category], 
                    system_prompt,
                    description
                )
            all_relations.extend(relations)
        
        # 验证和过滤关系
        valid_relations = []
        seen_relations = set()  # 用于去重
        
        for relation in all_relations:
            source_name = relation.get('source')
            target_name = relation.get('target')
            relation_type = relation.get('type')
            
            if (source_name in keyword_dict and target_name in keyword_dict and 
                source_name != target_name):
                
                # 创建关系的唯一标识符用于去重
                relation_key = (source_name, target_name, relation_type)
                reverse_key = (target_name, source_name, relation_type)
                
                # 避免重复关系（但prerequisite和contains是有方向性的，不算重复）
                if relation_key not in seen_relations:
                    # 对于related关系，避免反向重复
                    if relation_type == 'related' and reverse_key in seen_relations:
                        continue
                    
                    relation['source_keyword'] = keyword_dict[source_name]
                    relation['target_keyword'] = keyword_dict[target_name]
                    valid_relations.append(relation)
                    seen_relations.add(relation_key)
        
        current_app.logger.info(f"关键词关系分析完成，发现 {len(valid_relations)} 个有效关系")
        return valid_relations
    
    def _create_batches(self, items, batch_size):
        """创建批次"""
        return [items[i:i + batch_size] for i in range(0, len(items), batch_size)]
    
    def _analyze_cross_level_relations(self, higher_level_keywords, lower_level_keywords, system_prompt, description):
        """分析跨级别关系"""
        if not higher_level_keywords or not lower_level_keywords:
            return []
        
        # 组合所有关键词进行分析
        combined_keywords = higher_level_keywords + lower_level_keywords
        
        current_app.logger.info(f"正在分析{description}，高级别{len(higher_level_keywords)}个，低级别{len(lower_level_keywords)}个")
        
        keywords_text = ", ".join(combined_keywords)
        
        # 构建特定的提示词，强调跨级别关系
        cross_level_prompt = system_prompt + f"""

当前分析场景：{description}
前{len(higher_level_keywords)}个关键词是更高层级的概念，后{len(lower_level_keywords)}个是更具体的概念。
请特别关注：
1. 高层级概念包含(contains)低层级概念的关系
2. 高层级概念作为低层级概念前置知识(prerequisite)的关系
3. 同层级概念之间的相关(related)关系
"""
        
        try:
            response = self.client.chat.completions.create(
                model="THUDM/GLM-Z1-9B-0414",
                messages=[
                    {"role": "system", "content": cross_level_prompt},
                    {"role": "user", "content": f"请分析以下关键词之间的关系：\n{keywords_text}"}
                ],
                temperature=0.1,
                max_tokens=8192
            )
            
            result_text = response.choices[0].message.content
            
            # 解析JSON结果
            try:
                batch_result = json.loads(result_text)
                if 'relations' in batch_result:
                    current_app.logger.info(f"{description}分析完成，发现{len(batch_result['relations'])}个关系")
                    return batch_result['relations']
            except json.JSONDecodeError:
                # 尝试提取JSON部分
                json_pattern = r'(\{[\s\S]*\})'
                match = re.search(json_pattern, result_text)
                if match:
                    try:
                        batch_result = json.loads(match.group(1))
                        if 'relations' in batch_result:
                            current_app.logger.info(f"{description}分析完成，发现{len(batch_result['relations'])}个关系")
                            return batch_result['relations']
                    except:
                        current_app.logger.warning(f"无法解析{description}的关系结果: {result_text}")
                else:
                    current_app.logger.warning(f"无法找到{description}的JSON格式结果: {result_text}")
                    
        except Exception as e:
            current_app.logger.error(f"{description}关系分析失败: {str(e)}")
        
        return []
    
    def _analyze_same_level_relations(self, keywords, system_prompt, description):
        """分析同级别关系"""
        if len(keywords) < 2:
            return []
        
        current_app.logger.info(f"正在分析{description}关系，共{len(keywords)}个关键词")
        
        keywords_text = ", ".join(keywords)
        
        # 针对同级别关系的提示词
        same_level_prompt = system_prompt + f"""

当前分析场景：{description}关系
这些关键词都属于同一层级，请重点分析：
1. 相关(related)关系 - 概念之间的关联性
2. 前置(prerequisite)关系 - 学习顺序的依赖性
注意：同级别概念之间一般不存在包含(contains)关系
"""
        
        try:
            response = self.client.chat.completions.create(
                model="THUDM/GLM-Z1-9B-0414",
                messages=[
                    {"role": "system", "content": same_level_prompt},
                    {"role": "user", "content": f"请分析以下同级别关键词之间的关系：\n{keywords_text}"}
                ],
                temperature=0.1,
                max_tokens=8192
            )
            
            result_text = response.choices[0].message.content
            
            # 解析JSON结果
            try:
                batch_result = json.loads(result_text)
                if 'relations' in batch_result:
                    current_app.logger.info(f"{description}分析完成，发现{len(batch_result['relations'])}个关系")
                    return batch_result['relations']            
            except json.JSONDecodeError:
                json_pattern = r'(\{[\s\S]*\})'
                match = re.search(json_pattern, result_text)
                if match:
                    try:
                        batch_result = json.loads(match.group(1))
                        if 'relations' in batch_result:
                            return batch_result['relations']
                    except:
                        current_app.logger.warning(f"无法解析{description}的关系结果")
                        
        except Exception as e:
            current_app.logger.error(f"{description}关系分析失败: {str(e)}")
            return []
    
    def _analyze_specific_points_relations(self, specific_points, system_prompt):
        """分析具体知识点关系（使用滑动窗口）"""
        if len(specific_points) < 2:
            return []
        
        current_app.logger.info(f"使用滑动窗口分析具体知识点关系，共{len(specific_points)}个")
        
        all_relations = []
        window_size = 20
        overlap_size = 8  # 增加重叠大小以确保关系不被遗漏
        
        # 计算窗口数量用于tqdm进度展示
        windows = []
        for i in range(0, len(specific_points), window_size - overlap_size):
            window_keywords = specific_points[i:i + window_size]
            if len(window_keywords) >= 2:
                windows.append((i, window_keywords))
        
        # 使用tqdm显示滑动窗口分析进度
        for i, window_keywords in tqdm(windows, desc="具体知识点滑动窗口分析", unit="窗口"):
            window_num = i // (window_size - overlap_size) + 1
            relations = self._analyze_same_level_relations(
                window_keywords, 
                system_prompt,
                f"具体知识点窗口{window_num}"
            )
            all_relations.extend(relations)
        
        return all_relations
    
    def _save_relations_to_db(self, relations):
        """保存关系到数据库"""
        for relation in relations:
            source_keyword = relation['source_keyword']
            target_keyword = relation['target_keyword']
            
            # 检查关系是否已存在
            existing_relation = KeywordRelation.query.filter_by(
                source_keyword_id=source_keyword.id,
                target_keyword_id=target_keyword.id,
                relation_type=relation['type']
            ).first()
            
            if not existing_relation:
                keyword_relation = KeywordRelation(
                    source_keyword_id=source_keyword.id,
                    target_keyword_id=target_keyword.id,
                    relation_type=relation['type'],
                    strength=relation.get('strength', 1.0),
                    description=relation.get('description', '')
                )
                db.session.add(keyword_relation)
        
        db.session.commit()
        current_app.logger.info(f"关键词关系保存完成，共保存 {len(relations)} 个关系")
    
    def _update_course_keyword_stats(self, course_id):
        """更新课程关键词统计信息"""
        # 计算每个关键词在课程中的统计信息
        keyword_stats = db.session.query(
            Keyword.id,
            func.count(VideoKeyword.video_id).label('video_count'),
            func.avg(VideoKeyword.weight).label('avg_weight')
        ).join(VideoKeyword).join(Video).join(Course).filter(
            Course.id == course_id
        ).group_by(Keyword.id).all()
        
        for keyword_id, video_count, avg_weight in keyword_stats:
            # 检查课程关键词关系是否已存在
            existing_course_keyword = CourseKeyword.query.filter_by(
                course_id=course_id,
                keyword_id=keyword_id
            ).first()
            
            if existing_course_keyword:
                existing_course_keyword.video_count = video_count
                existing_course_keyword.avg_weight = float(avg_weight) if avg_weight else 0.0
                existing_course_keyword.update_time = datetime.now()
            else:
                course_keyword = CourseKeyword(
                    course_id=course_id,
                    keyword_id=keyword_id,
                    video_count=video_count,
                    avg_weight=float(avg_weight) if avg_weight else 0.0
                )
                db.session.add(course_keyword)
        
        db.session.commit()
        current_app.logger.info(f"课程关键词统计更新完成，共更新 {len(keyword_stats)} 个关键词")

def process_knowledge_graph_task(course_id, force_regenerate=False, stop_flag=None, incremental=True):
    """
    处理知识图谱任务的主函数
    
    参数:
        course_id: 课程ID
        force_regenerate: 是否强制重新生成
        stop_flag: 停止标志(threading.Event)，如果设置则中断处理
        incremental: 是否使用增量处理（默认为True）
    """
    processor = KnowledgeGraphProcessor()
    return processor.process_course_knowledge_graph(course_id, force_regenerate, stop_flag, incremental)

def trigger_knowledge_graph_generation(course_id, force_regenerate=False, incremental=True):
    """触发知识图谱生成（同步方式，用于兼容）"""
    processor = KnowledgeGraphProcessor()
    return processor.process_course_knowledge_graph(course_id, force_regenerate, incremental=incremental)
    return processor.process_course_knowledge_graph(course_id, force_regenerate)
