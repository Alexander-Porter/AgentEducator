#!/usr/bin/env python3
"""
检查孤儿向量索引脚本（专门检查向量索引）
检查所有不属于任何有效视频的向量索引数据和文件
"""

import os
import sys
from datetime import datetime
from sqlalchemy import text

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
app = create_app()
from models.models import (
    db, Video, VideoVectorIndex, Course
)

def get_orphaned_vector_indices():
    """获取所有孤儿向量索引（video_id为NULL或指向不存在/已删除视频的索引）"""
    orphaned_indices = []
    
    # 查找video_id为NULL的向量索引
    null_video_indices = VideoVectorIndex.query.filter(VideoVectorIndex.video_id.is_(None)).all()
    if null_video_indices:
        print(f"发现 {len(null_video_indices)} 个video_id为NULL的向量索引:")
        for index in null_video_indices:
            print(f"  - ID: {index.id}, 索引路径: '{index.index_path}', 视频ID: NULL")
    
    orphaned_indices.extend(null_video_indices)
    
    # 查找video_id指向不存在视频的向量索引
    invalid_video_indices = db.session.query(VideoVectorIndex).outerjoin(
        Video, VideoVectorIndex.video_id == Video.id
    ).filter(
        VideoVectorIndex.video_id.isnot(None),
        Video.id.is_(None)
    ).all()
    
    if invalid_video_indices:
        print(f"发现 {len(invalid_video_indices)} 个video_id指向不存在视频的向量索引:")
        for index in invalid_video_indices:
            print(f"  - ID: {index.id}, 索引路径: '{index.index_path}', 视频ID: {index.video_id} (不存在)")
    
    orphaned_indices.extend(invalid_video_indices)
    
    # 查找video_id指向已删除视频的向量索引
    deleted_video_indices = db.session.query(VideoVectorIndex).join(
        Video, VideoVectorIndex.video_id == Video.id
    ).filter(
        Video.is_deleted == True
    ).all()
    
    if deleted_video_indices:
        print(f"发现 {len(deleted_video_indices)} 个video_id指向已删除视频的向量索引:")
        for index in deleted_video_indices:
            video = Video.query.get(index.video_id)
            print(f"  - ID: {index.id}, 索引路径: '{index.index_path}', 视频ID: {index.video_id} (已删除), 视频标题: '{video.title if video else 'N/A'}'")
    
    orphaned_indices.extend(deleted_video_indices)
      # 查找video存在但课程不存在或已删除的向量索引
    orphaned_by_course_indices = db.session.query(VideoVectorIndex).join(
        Video, VideoVectorIndex.video_id == Video.id
    ).outerjoin(
        Course, Video.course_id == Course.id
    ).filter(
        Video.is_deleted == False,  # 只考虑未删除的视频
        db.or_(
            Video.course_id.is_(None),  # 课程ID为空
            Course.id.is_(None),        # 课程不存在
            Course.is_deleted == True   # 课程已删除
        )
    ).all()
    
    if orphaned_by_course_indices:
        print(f"发现 {len(orphaned_by_course_indices)} 个关联视频无有效课程的向量索引:")
        for index in orphaned_by_course_indices:
            video = Video.query.get(index.video_id)
            if video:
                course = Course.query.get(video.course_id) if video.course_id else None
                if video.course_id is None:
                    status = "课程ID为空"
                elif course is None:
                    status = f"课程ID: {video.course_id} (不存在)"
                elif course.is_deleted:
                    status = f"课程ID: {video.course_id} (已删除)"
                else:
                    status = "未知状态"
                print(f"  - ID: {index.id}, 索引路径: '{index.index_path}', 视频ID: {index.video_id}, {status}")
            else:
                print(f"  - ID: {index.id}, 索引路径: '{index.index_path}', 视频ID: {index.video_id}, 视频不存在")
    
    orphaned_indices.extend(orphaned_by_course_indices)
    
    # 查找course_id为NULL的视频的向量索引（这部分已经包含在上面了，但为了清晰性保留）
    null_course_video_indices = db.session.query(VideoVectorIndex).join(
        Video, VideoVectorIndex.video_id == Video.id
    ).filter(
        Video.is_deleted == False,  # 只考虑未删除的视频
        Video.course_id.is_(None)
    ).all()    
    if null_course_video_indices:
        print(f"发现 {len(null_course_video_indices)} 个关联视频course_id为NULL的向量索引:")
        for index in null_course_video_indices:
            video = Video.query.get(index.video_id)
            print(f"  - ID: {index.id}, 索引路径: '{index.index_path}', 视频ID: {index.video_id}, 视频标题: '{video.title if video else 'N/A'}'")
    
    # 注意：这些记录已经包含在orphaned_by_course_indices中了，所以不重复添加
    # orphaned_indices.extend(null_course_video_indices)
    
    return orphaned_indices

def check_vector_index_files():
    """检查向量索引文件系统中的孤儿文件"""
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    vector_indices_dir = os.path.join(backend_dir, 'vector_indices')
    
    if not os.path.exists(vector_indices_dir):
        print("向量索引目录不存在")
        return []
      # 获取所有有效的video_id（未删除且课程未删除的视频）
    valid_video_ids = set()
    valid_videos = db.session.query(Video).join(Course).filter(
        Video.is_deleted == False,
        Course.is_deleted == False
    ).all()
    for video in valid_videos:
        valid_video_ids.add(str(video.id))
    
    print(f"有效视频数量: {len(valid_video_ids)}")
    
    # 检查文件系统中的向量索引目录
    orphaned_dirs = []
    orphaned_files = []
    
    for item in os.listdir(vector_indices_dir):
        item_path = os.path.join(vector_indices_dir, item)
        
        if os.path.isdir(item_path):
            # 检查是否是video_开头的目录
            if item.startswith('video_'):
                video_id = item[6:]  # 去掉'video_'前缀
                if video_id not in valid_video_ids:
                    orphaned_dirs.append(item_path)
            else:
                # 其他不符合命名规范的目录
                orphaned_dirs.append(item_path)
        
        elif os.path.isfile(item_path):
            # 检查是否是孤儿文件
            orphaned_files.append(item_path)
    
    print(f"孤儿向量索引目录: {len(orphaned_dirs)} 个")
    for dir_path in orphaned_dirs[:5]:  # 只显示前5个
        size = get_directory_size(dir_path)
        print(f"  - {dir_path} ({format_size(size)})")
    if len(orphaned_dirs) > 5:
        print(f"  ... 还有 {len(orphaned_dirs) - 5} 个目录")
    
    print(f"孤儿向量索引文件: {len(orphaned_files)} 个")
    for file_path in orphaned_files[:5]:  # 只显示前5个
        size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        print(f"  - {file_path} ({format_size(size)})")
    if len(orphaned_files) > 5:
        print(f"  ... 还有 {len(orphaned_files) - 5} 个文件")
    
    return orphaned_dirs + orphaned_files

def get_directory_size(directory):
    """计算目录大小"""
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                if os.path.exists(file_path):
                    total_size += os.path.getsize(file_path)
    except Exception as e:
        print(f"计算目录大小时出错 {directory}: {e}")
    return total_size

def format_size(size_bytes):
    """格式化文件大小"""
    if size_bytes == 0:
        return "0 B"
    elif size_bytes > 1024 * 1024 * 1024:  # GB
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
    elif size_bytes > 1024 * 1024:  # MB
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    elif size_bytes > 1024:  # KB
        return f"{size_bytes / 1024:.2f} KB"
    else:
        return f"{size_bytes} B"

def check_database_consistency():
    """检查数据库中向量索引的一致性"""
    # 检查索引路径是否存在
    all_indices = VideoVectorIndex.query.all()
    missing_files = []
    invalid_paths = []
    
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    
    for index in all_indices:
        if index.index_path:
            # 构建完整路径
            if index.index_path.startswith('/') or index.index_path.startswith('\\'):
                full_path = os.path.join(backend_dir, index.index_path.lstrip('/\\'))
            else:
                full_path = os.path.join(backend_dir, index.index_path)
            
            if not os.path.exists(full_path):
                missing_files.append({
                    'index_id': index.id,
                    'video_id': index.video_id,
                    'path': index.index_path,
                    'full_path': full_path
                })
        else:
            invalid_paths.append({
                'index_id': index.id,
                'video_id': index.video_id
            })
    
    if missing_files:
        print(f"数据库中存在但文件不存在的索引: {len(missing_files)} 个")
        for item in missing_files[:3]:
            print(f"  - 索引ID: {item['index_id']}, 视频ID: {item['video_id']}, 路径: {item['path']}")
        if len(missing_files) > 3:
            print(f"  ... 还有 {len(missing_files) - 3} 个")
    
    if invalid_paths:
        print(f"索引路径为空的记录: {len(invalid_paths)} 个")
        for item in invalid_paths[:3]:
            print(f"  - 索引ID: {item['index_id']}, 视频ID: {item['video_id']}")
        if len(invalid_paths) > 3:
            print(f"  ... 还有 {len(invalid_paths) - 3} 个")
    
    return missing_files, invalid_paths

def main():
    """主函数"""
    print("=" * 60)
    print("孤儿向量索引检查报告")
    print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    with app.app_context():
        try:
            # 检查向量索引目录整体情况
            backend_dir = os.path.dirname(os.path.abspath(__file__))
            vector_indices_dir = os.path.join(backend_dir, 'vector_indices')
            
            if os.path.exists(vector_indices_dir):
                total_size = get_directory_size(vector_indices_dir)
                item_count = len(os.listdir(vector_indices_dir))
                print(f"向量索引目录总大小: {format_size(total_size)}")
                print(f"向量索引目录项目数量: {item_count}")
            else:
                print("向量索引目录不存在")
                return
            
            print("\n" + "-" * 40)
            print("1. 检查数据库中的孤儿向量索引...")
            print("-" * 40)
            
            # 获取所有孤儿向量索引
            orphaned_indices = get_orphaned_vector_indices()
            
            if orphaned_indices:
                print(f"\n⚠️  发现 {len(orphaned_indices)} 个孤儿向量索引记录")
                
                # 计算这些索引占用的存储空间
                total_orphaned_size = 0
                for index in orphaned_indices:
                    if index.index_path:
                        if index.index_path.startswith('/') or index.index_path.startswith('\\'):
                            full_path = os.path.join(backend_dir, index.index_path.lstrip('/\\'))
                        else:
                            full_path = os.path.join(backend_dir, index.index_path)
                        
                        if os.path.exists(full_path):
                            if os.path.isdir(full_path):
                                total_orphaned_size += get_directory_size(full_path)
                            else:
                                total_orphaned_size += os.path.getsize(full_path)
                
                print(f"孤儿索引占用存储空间: {format_size(total_orphaned_size)}")
            else:
                print("✅ 数据库中未发现孤儿向量索引记录")
            
            print("\n" + "-" * 40)
            print("2. 检查文件系统中的孤儿向量索引...")
            print("-" * 40)
            
            # 检查文件系统中的孤儿向量索引
            orphaned_files = check_vector_index_files()
            
            if orphaned_files:
                total_file_size = 0
                for file_path in orphaned_files:
                    if os.path.exists(file_path):
                        if os.path.isdir(file_path):
                            total_file_size += get_directory_size(file_path)
                        else:
                            total_file_size += os.path.getsize(file_path)
                
                print(f"文件系统孤儿索引占用存储空间: {format_size(total_file_size)}")
            else:
                print("✅ 文件系统中未发现孤儿向量索引")
            
            print("\n" + "-" * 40)
            print("3. 检查数据库与文件系统一致性...")
            print("-" * 40)
            
            # 检查数据库一致性
            missing_files, invalid_paths = check_database_consistency()
            
            if not missing_files and not invalid_paths:
                print("✅ 数据库与文件系统一致")
            
            # 统计信息
            print("\n" + "=" * 60)
            print("检查汇总:")
            
            if orphaned_indices:
                print(f"📊 数据库孤儿索引记录: {len(orphaned_indices)} 个")
            
            if orphaned_files:
                print(f"📊 文件系统孤儿索引: {len(orphaned_files)} 个")
            
            if missing_files:
                print(f"📊 数据库有记录但文件不存在: {len(missing_files)} 个")
            
            if invalid_paths:
                print(f"📊 索引路径为空的记录: {len(invalid_paths)} 个")
            
            print("\n如需清理，请运行相应的清理脚本")
            print("=" * 60)
            
        except Exception as e:
            print(f"检查过程中发生错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            db.session.close()

if __name__ == "__main__":
    main()
