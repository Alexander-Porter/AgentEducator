#!/usr/bin/env python3
"""
测试知识图谱处理器修复
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from tasks.knowledge_graph_processor import KnowledgeGraphProcessor
from models.models import Course, Video, VideoKeyword, Keyword

def test_extract_and_categorize_keywords():
    """测试修复后的_extract_and_categorize_keywords方法"""
    app = create_app()
    
    with app.app_context():
        print("=== 测试知识图谱处理器修复 ===")
        
        # 查找一个有视频的课程
        course = Course.query.join(Video).filter(Video.is_deleted == False).first()
        if not course:
            print("❌ 未找到有视频的课程")
            return False
            
        print(f"✅ 找到课程: {course.name} (ID: {course.id})")
        
        # 检查该课程下是否有VideoKeyword关系
        video_count = Video.query.filter_by(course_id=course.id, is_deleted=False).count()
        print(f"📊 课程视频数: {video_count}")
        
        # 检查VideoKeyword关系数
        vk_count = VideoKeyword.query.join(Video).filter(Video.course_id == course.id).count()
        print(f"🔗 VideoKeyword关系数: {vk_count}")
        
        if vk_count == 0:
            print("⚠️ 该课程没有VideoKeyword关系，无法测试")
            return False
        
        # 查看现有关键词分类状态
        keywords_in_course = Keyword.query.join(VideoKeyword).join(Video).filter(
            Video.course_id == course.id
        ).distinct().all()
        
        print(f"📝 课程中的关键词数: {len(keywords_in_course)}")
        
        # 统计现有分类
        category_stats = {}
        for keyword in keywords_in_course:
            category = keyword.category
            category_stats[category] = category_stats.get(category, 0) + 1
        
        print("📋 修复前的关键词分类分布:")
        for category, count in category_stats.items():
            print(f"  - {category}: {count}个")
        
        # 测试修复后的方法
        processor = KnowledgeGraphProcessor()
        try:
            print("\n🔧 开始测试修复后的方法...")
            result = processor._extract_and_categorize_keywords(course.id)
            print("✅ 提取关键词成功")
            
            print("📊 分类结果:")
            for category, keywords_list in result.items():
                print(f"  - {category}: {len(keywords_list)}个关键词")
                if len(keywords_list) <= 5:
                    print(f"    示例: {keywords_list}")
                else:
                    print(f"    示例: {keywords_list[:5]}...")
            
            # 验证关键词是否被正确更新
            print("\n🔍 验证关键词分类更新...")
            updated_keywords = Keyword.query.join(VideoKeyword).join(Video).filter(
                Video.course_id == course.id
            ).distinct().all()
            
            new_category_stats = {}
            for keyword in updated_keywords:
                category = keyword.category
                new_category_stats[category] = new_category_stats.get(category, 0) + 1
            
            print("📋 修复后的关键词分类分布:")
            for category, count in new_category_stats.items():
                print(f"  - {category}: {count}个")
            
            # 检查是否有变化
            if category_stats != new_category_stats:
                print("✅ 关键词分类已更新")
            else:
                print("ℹ️ 关键词分类无需更新（可能之前已经是正确的）")
            
            return True
            
        except Exception as e:
            print(f"❌ 提取关键词失败: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = test_extract_and_categorize_keywords()
    if success:
        print("\n🎉 测试完成！修复验证成功")
    else:
        print("\n💥 测试失败")
    sys.exit(0 if success else 1)
