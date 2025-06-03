#!/usr/bin/env python3
"""
检查知识图谱相关数据的脚本
"""

from app import create_app
app = create_app()
from models.models import db, Course, Keyword, CourseKeyword, VideoKeyword, KeywordRelation

with app.app_context():
    # 检查数据库中是否有课程
    print('=== 课程数据 ===')
    courses = Course.query.all()
    for course in courses:
        print(f'课程: {course.name} (ID: {course.id})')
    
    print(f'总课程数: {len(courses)}')
    
    # 检查是否有关键词数据
    print('\n=== 关键词数据 ===')
    keywords = Keyword.query.all()
    print(f'总关键词数: {len(keywords)}')
    for i, keyword in enumerate(keywords[:5]):  # 只显示前5个
        print(f'{i+1}. {keyword.name} (分类: {keyword.category})')
    
    # 检查课程关键词关系
    print('\n=== 课程关键词关系 ===')
    course_keywords = CourseKeyword.query.all()
    print(f'总课程关键词关系数: {len(course_keywords)}')
    for i, ck in enumerate(course_keywords[:5]):  # 只显示前5个
        course = Course.query.get(ck.course_id)
        keyword = Keyword.query.get(ck.keyword_id)
        print(f'{i+1}. 课程: {course.name if course else "未知"} - 关键词: {keyword.name if keyword else "未知"} (视频数: {ck.video_count}, 平均权重: {ck.avg_weight})')
    
    # 检查关键词关系
    print('\n=== 关键词关系 ===')
    relations = KeywordRelation.query.all()
    print(f'总关键词关系数: {len(relations)}')
    for i, rel in enumerate(relations[:5]):  # 只显示前5个
        source = Keyword.query.get(rel.source_keyword_id)
        target = Keyword.query.get(rel.target_keyword_id)
        print(f'{i+1}. {source.name if source else "未知"} -> {target.name if target else "未知"} (类型: {rel.relation_type}, 强度: {rel.strength})')
    
    # 检查特定课程的知识图谱数据
    if courses:
        first_course = courses[0]
        print(f'\n=== 课程 "{first_course.name}" 的知识图谱数据 ===')
        
        # 获取该课程的关键词
        course_keywords = db.session.query(
            Keyword, CourseKeyword
        ).join(CourseKeyword).filter(
            CourseKeyword.course_id == first_course.id
        ).all()
        
        print(f'该课程关键词数: {len(course_keywords)}')
        for keyword, course_keyword in course_keywords[:10]:  # 显示前10个
            print(f'- {keyword.name} (分类: {keyword.category}, 视频数: {course_keyword.video_count}, 平均权重: {course_keyword.avg_weight})')
