# 关键词数据库结构使用指南

## 概述

本项目采用了标准化的关键词数据库设计，支持多层级关键词管理、视频和课程的关键词关联、以及关键词之间的关系建模。

## 数据库表结构

### 核心表

1. **Keyword** - 关键词主表
   - `id`: 关键词唯一标识 (UUID)
   - `name`: 关键词名称 (唯一)
   - `category`: 分类 (core_concept/main_module/specific_point)
   - `description`: 描述

2. **VideoKeyword** - 视频关键词关系表 (多对多)
   - `video_id`: 视频ID
   - `keyword_id`: 关键词ID
   - `weight`: 权重 (0-1，表示关键词在视频中的重要程度)

3. **CourseKeyword** - 课程关键词关系表 (多对多)
   - `course_id`: 课程ID
   - `keyword_id`: 关键词ID
   - `video_count`: 包含该关键词的视频数量
   - `avg_weight`: 该关键词在课程中的平均权重

4. **KeywordRelation** - 关键词关系表
   - `source_keyword_id`: 源关键词ID
   - `target_keyword_id`: 目标关键词ID
   - `relation_type`: 关系类型 (prerequisite/related/contains)
   - `strength`: 关系强度 (0-1)

## 迁移指南

### 从VideoSummary迁移

1. **运行迁移脚本**
```bash
cd backend/migrations
python migrate_video_summary_keywords.py --backup --dry-run
```

2. **参数说明**
- `--dry-run`: 试运行，不实际修改数据库
- `--backup`: 备份原始数据
- `--clear-old`: 清理VideoSummary中的旧关键词字段

3. **迁移步骤**
- 从VideoSummary.keywords字段提取逗号分隔的关键词
- 创建或更新Keyword表记录
- 建立VideoKeyword关系
- 根据VideoKeyword统计生成CourseKeyword关系

## API使用示例

### 1. 查询视频关键词

```http
GET /api/knowledge-graph/video/{video_id}/keywords
```

**响应示例:**
```json
{
  "code": 200,
  "msg": "获取视频关键词成功",
  "data": {
    "video_info": {
      "id": "video-uuid",
      "title": "Python基础教程",
      "description": "..."
    },
    "keywords": [
      {
        "id": "keyword-uuid",
        "name": "变量定义",
        "category": "specific_point",
        "description": "Python变量定义相关知识",
        "weight": 0.8,
        "create_time": "2023-01-01 10:00:00"
      }
    ],
    "total_count": 10
  }
}
```

### 2. 查询课程关键词

```http
GET /api/knowledge-graph/course/{course_id}/keywords?category=core_concept&limit=20
```

**响应示例:**
```json
{
  "code": 200,
  "msg": "获取课程关键词成功",
  "data": {
    "course_info": {
      "id": "course-uuid",
      "name": "Python编程基础",
      "description": "..."
    },
    "keywords": [
      {
        "id": "keyword-uuid",
        "name": "面向对象编程",
        "category": "core_concept",
        "description": "OOP核心概念",
        "video_count": 5,
        "avg_weight": 0.75,
        "importance_score": 3.75
      }
    ],
    "total_count": 15,
    "category_stats": {
      "core_concept": 5,
      "main_module": 8,
      "specific_point": 25
    }
  }
}
```

### 3. 查询关键词使用情况

```http
GET /api/knowledge-graph/keyword/{keyword_id}/usage
```

**响应示例:**
```json
{
  "code": 200,
  "msg": "获取关键词使用情况成功",
  "data": {
    "keyword_info": {
      "id": "keyword-uuid",
      "name": "函数定义",
      "category": "main_module",
      "description": "..."
    },
    "usage_summary": {
      "total_videos": 8,
      "total_courses": 3,
      "avg_weight": 0.65
    },
    "videos": [
      {
        "id": "video-uuid",
        "title": "Python函数基础",
        "duration": 1200,
        "weight": 0.9,
        "course_id": "course-uuid",
        "course_name": "Python基础"
      }
    ],
    "courses": [
      {
        "id": "course-uuid",
        "name": "Python基础",
        "video_count": 5,
        "avg_weight": 0.75
      }
    ]
  }
}
```

### 4. 搜索关键词

```http
GET /api/knowledge-graph/search?q=Python&category=core_concept&courseId=course-uuid&limit=10
```

## 代码使用示例

### 1. 为视频添加关键词

```python
from models.models import db, Keyword, VideoKeyword

def add_keywords_to_video(video_id, keyword_names_with_weights):
    """
    为视频添加关键词
    
    参数:
        video_id: 视频ID
        keyword_names_with_weights: [(关键词名, 权重), ...]
    """
    for keyword_name, weight in keyword_names_with_weights:
        # 查找或创建关键词
        keyword = Keyword.query.filter_by(name=keyword_name).first()
        if not keyword:
            keyword = Keyword(
                name=keyword_name,
                category='specific_point',  # 默认分类
                description=f"关键词: {keyword_name}"
            )
            db.session.add(keyword)
            db.session.flush()
        
        # 检查关系是否已存在
        existing_relation = VideoKeyword.query.filter_by(
            video_id=video_id,
            keyword_id=keyword.id
        ).first()
        
        if not existing_relation:
            video_keyword = VideoKeyword(
                video_id=video_id,
                keyword_id=keyword.id,
                weight=weight
            )
            db.session.add(video_keyword)
    
    db.session.commit()
```

### 2. 查询视频的关键词

```python
def get_video_keywords(video_id):
    """获取视频的所有关键词"""
    return db.session.query(
        Keyword, VideoKeyword
    ).join(VideoKeyword).filter(
        VideoKeyword.video_id == video_id
    ).order_by(VideoKeyword.weight.desc()).all()
```

### 3. 查询课程的关键词统计

```python
def get_course_keyword_stats(course_id):
    """获取课程的关键词统计"""
    return db.session.query(
        Keyword, CourseKeyword
    ).join(CourseKeyword).filter(
        CourseKeyword.course_id == course_id
    ).order_by(
        CourseKeyword.video_count.desc(),
        CourseKeyword.avg_weight.desc()
    ).all()
```

### 4. 更新课程关键词统计

```python
def update_course_keyword_stats(course_id):
    """更新课程关键词统计"""
    # 统计该课程下每个关键词的使用情况
    keyword_stats = db.session.query(
        Keyword.id,
        db.func.count(VideoKeyword.id).label('video_count'),
        db.func.avg(VideoKeyword.weight).label('avg_weight')
    ).join(VideoKeyword).join(Video).filter(
        Video.course_id == course_id,
        Video.is_deleted == False
    ).group_by(Keyword.id).all()
    
    for keyword_id, video_count, avg_weight in keyword_stats:
        course_keyword = CourseKeyword.query.filter_by(
            course_id=course_id,
            keyword_id=keyword_id
        ).first()
        
        if course_keyword:
            course_keyword.video_count = video_count
            course_keyword.avg_weight = float(avg_weight) if avg_weight else 0.0
        else:
            course_keyword = CourseKeyword(
                course_id=course_id,
                keyword_id=keyword_id,
                video_count=video_count,
                avg_weight=float(avg_weight) if avg_weight else 0.0
            )
            db.session.add(course_keyword)
    
    db.session.commit()
```

## 数据验证

运行验证脚本检查数据完整性：

```bash
cd backend/migrations
python validate_keyword_migration.py
```

验证项目包括：
- 关键词表数据完整性
- 视频-关键词关系
- 课程-关键词关系统计准确性
- 关键词分类分布
- 与VideoSummary的数据一致性

## 最佳实践

1. **关键词分类**
   - `core_concept`: 核心概念，课程的理论基础
   - `main_module`: 主要模块，较大的知识块
   - `specific_point`: 具体知识点，详细的技术点

2. **权重设置**
   - 0.0-0.3: 低重要性
   - 0.3-0.7: 中等重要性
   - 0.7-1.0: 高重要性

3. **关系类型**
   - `prerequisite`: 前置关系 (A是B的前置知识)
   - `related`: 相关关系 (A和B相关但无明确顺序)
   - `contains`: 包含关系 (A包含B)

4. **性能优化**
   - 使用索引优化查询
   - 批量操作时使用事务
   - 定期更新课程关键词统计

## 故障排除

### 常见问题

1. **重复关键词**
   - 检查唯一约束
   - 使用名称查重

2. **统计不准确**
   - 运行update_course_keyword_stats更新
   - 检查软删除视频是否正确过滤

3. **关系缺失**
   - 检查外键约束
   - 验证视频和课程是否存在

### 数据修复

如果发现数据问题，可以运行：

```bash
# 修复课程关键词统计
python fix_course_keywords.py

# 验证数据完整性
python validate_keyword_migration.py
```
