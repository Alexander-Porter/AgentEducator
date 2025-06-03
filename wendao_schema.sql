-- 闻道平台数据库结构
-- 基于现有数据设计创建的SQL文件

-- 创建用户表
CREATE TABLE `users` (
  `id` CHAR(36) NOT NULL,
  `username` VARCHAR(50) NOT NULL,
  `password` VARCHAR(255) NOT NULL,
  `email` VARCHAR(100) NOT NULL,
  `role` VARCHAR(20) NOT NULL COMMENT 'teacher, student',
  `avatar` VARCHAR(255),
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `is_deleted` BOOLEAN DEFAULT FALSE,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_username` (`username`),
  UNIQUE KEY `uk_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- 创建课程表
CREATE TABLE `courses` (
  `id` CHAR(36) NOT NULL,
  `name` VARCHAR(100) NOT NULL,
  `code` VARCHAR(20) NOT NULL,
  `description` TEXT,
  `image_url` VARCHAR(255),
  `start_date` DATETIME NOT NULL,
  `end_date` DATETIME NOT NULL,
  `hours` INT NOT NULL,
  `student_count` INT DEFAULT 0,
  `status` VARCHAR(20) NOT NULL COMMENT 'active, inactive',
  `semester` VARCHAR(20) NOT NULL,
  `teacher_id` CHAR(36) NOT NULL,
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `is_deleted` BOOLEAN DEFAULT FALSE,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_code` (`code`),
  KEY `idx_teacher` (`teacher_id`),
  CONSTRAINT `fk_course_teacher` FOREIGN KEY (`teacher_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='课程表';

-- 创建视频表
CREATE TABLE `videos` (
  `id` CHAR(36) NOT NULL,
  `title` VARCHAR(255) NOT NULL COMMENT '视频标题',
  `description` TEXT COMMENT '视频描述',
  `cover_url` VARCHAR(255) COMMENT '封面图URL',
  `video_url` VARCHAR(255) NOT NULL COMMENT '视频URL',
  `duration` INT NOT NULL DEFAULT 0 COMMENT '视频时长(秒)',
  `course_id` CHAR(36) NOT NULL COMMENT '所属课程ID',
  `view_count` INT DEFAULT 0 COMMENT '观看次数',
  `comment_count` INT DEFAULT 0 COMMENT '评论数量',
  `upload_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '上传时间',
  `is_deleted` BOOLEAN DEFAULT FALSE COMMENT '是否删除',
  `completed_count` INT DEFAULT 0 COMMENT '完成观看的人数',
  PRIMARY KEY (`id`),
  KEY `idx_course` (`course_id`),
  CONSTRAINT `fk_video_course` FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='视频资源表';

-- 创建视频评论表
CREATE TABLE `video_comments` (
  `id` CHAR(36) NOT NULL,
  `content` TEXT NOT NULL,
  `video_id` CHAR(36) NOT NULL,
  `user_id` CHAR(36) NOT NULL,
  `parent_id` CHAR(36) DEFAULT NULL COMMENT '回复的评论ID',
  `time_point` INT DEFAULT NULL COMMENT '视频时间点（秒）',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `likes` INT DEFAULT 0,
  `is_deleted` BOOLEAN DEFAULT FALSE,
  PRIMARY KEY (`id`),
  KEY `idx_video` (`video_id`),
  KEY `idx_user` (`user_id`),
  KEY `idx_parent` (`parent_id`),
  CONSTRAINT `fk_comment_video` FOREIGN KEY (`video_id`) REFERENCES `videos` (`id`),
  CONSTRAINT `fk_comment_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `fk_comment_parent` FOREIGN KEY (`parent_id`) REFERENCES `video_comments` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='视频评论表';

-- 创建评论点赞记录表
CREATE TABLE `comment_likes` (
  `id` CHAR(36) NOT NULL,
  `comment_id` CHAR(36) NOT NULL,
  `user_id` CHAR(36) NOT NULL,
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_comment_like` (`comment_id`, `user_id`),
  KEY `idx_comment` (`comment_id`),
  KEY `idx_user` (`user_id`),
  CONSTRAINT `fk_like_comment` FOREIGN KEY (`comment_id`) REFERENCES `video_comments` (`id`),
  CONSTRAINT `fk_like_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='评论点赞记录表';

-- 创建用户视频进度表
CREATE TABLE `user_video_progress` (
  `id` CHAR(36) NOT NULL,
  `user_id` CHAR(36) NOT NULL,
  `video_id` CHAR(36) NOT NULL,
  `progress` FLOAT DEFAULT 0 COMMENT '进度（0-1之间）',
  `last_position` INT DEFAULT 0 COMMENT '上次观看位置（秒）',
  `completed` BOOLEAN DEFAULT FALSE,
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_user_video` (`user_id`, `video_id`),
  CONSTRAINT `fk_progress_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `fk_progress_video` FOREIGN KEY (`video_id`) REFERENCES `videos` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户视频进度表';

-- 创建文档表
CREATE TABLE `documents` (
  `id` CHAR(36) NOT NULL COMMENT '文档ID',
  `title` VARCHAR(255) NOT NULL COMMENT '文档标题',
  `file_url` VARCHAR(255) NOT NULL COMMENT '文件URL',
  `file_type` VARCHAR(50) NOT NULL COMMENT '文件类型',
  `file_size` INT DEFAULT 0 COMMENT '文件大小(字节)',
  `course_id` CHAR(36) NOT NULL COMMENT '所属课程ID',
  `upload_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '上传时间',
  `is_deleted` BOOLEAN DEFAULT FALSE COMMENT '是否删除',
  PRIMARY KEY (`id`),
  KEY `idx_course` (`course_id`),
  CONSTRAINT `fk_document_course` FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='课程文档资料表';

-- 创建视频摘要表
CREATE TABLE `video_summaries` (
  `id` CHAR(36) NOT NULL,
  `video_id` CHAR(36) NOT NULL,
  `main_points` TEXT COMMENT '主要观点',
  `keywords` VARCHAR(255) COMMENT '逗号分隔的关键词',
  `sections` TEXT COMMENT 'JSON格式存储的章节摘要',
  `generate_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_video` (`video_id`),
  CONSTRAINT `fk_summary_video` FOREIGN KEY (`video_id`) REFERENCES `videos` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='视频摘要表';

-- 创建学生选课表
CREATE TABLE `student_course_enrollments` (
  `id` CHAR(36) NOT NULL,
  `student_id` CHAR(36) NOT NULL,
  `course_id` CHAR(36) NOT NULL,
  `enroll_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_student_course` (`student_id`, `course_id`),
  KEY `idx_student` (`student_id`),
  KEY `idx_course` (`course_id`),
  CONSTRAINT `fk_enrollment_student` FOREIGN KEY (`student_id`) REFERENCES `users` (`id`),
  CONSTRAINT `fk_enrollment_course` FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学生选课表';

-- 创建用户权限表
CREATE TABLE `user_permission` (
  `id` CHAR(36) NOT NULL,
  `user_id` CHAR(36) NOT NULL,
  `course_access` TEXT COMMENT 'JSON格式的课程ID列表',
  `comment_enabled` BOOLEAN DEFAULT TRUE,
  `download_enabled` BOOLEAN DEFAULT FALSE,
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_user` (`user_id`),
  CONSTRAINT `fk_permission_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户权限表';

-- 创建视频关键帧表
CREATE TABLE `video_keyframes` (
  `id` INT AUTO_INCREMENT NOT NULL,
  `video_id` CHAR(36) NOT NULL,
  `frame_number` INT NOT NULL,
  `time_point` FLOAT NOT NULL COMMENT '时间点(秒)',
  `time_formatted` VARCHAR(20) COMMENT '格式化时间',
  `file_name` VARCHAR(255) COMMENT '关键帧图片文件名',
  `ocr_result` TEXT COMMENT 'OCR识别结果(JSON)',
  `asr_texts` TEXT COMMENT '语音识别文本',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_video` (`video_id`),
  KEY `idx_time` (`time_point`),
  CONSTRAINT `fk_keyframe_video` FOREIGN KEY (`video_id`) REFERENCES `videos` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='视频关键帧表';

-- 创建视频处理任务表
CREATE TABLE `video_processing_tasks` (
  `id` CHAR(36) NOT NULL,
  `video_id` CHAR(36) NOT NULL COMMENT '关联的视频ID',
  `task_id` VARCHAR(50) NOT NULL COMMENT '处理任务ID',
  `status` VARCHAR(20) NOT NULL COMMENT '处理状态：pending, processing, completed, failed',
  `processing_type` VARCHAR(20) NOT NULL COMMENT '处理类型：transcoding, thumbnail, subtitle, all',
  `progress` FLOAT DEFAULT 0.0 COMMENT '处理进度，0-100',
  `error_message` TEXT COMMENT '错误信息',
  `start_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '开始时间',
  `end_time` DATETIME COMMENT '结束时间',
  PRIMARY KEY (`id`),
  KEY `idx_video` (`video_id`),
  KEY `idx_task` (`task_id`),
  CONSTRAINT `fk_task_video` FOREIGN KEY (`video_id`) REFERENCES `videos` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='视频处理任务表';

-- 创建视频向量索引表
CREATE TABLE `video_vector_indices` (
  `id` INT AUTO_INCREMENT NOT NULL,
  `video_id` CHAR(36) NOT NULL,
  `index_path` VARCHAR(255) NOT NULL COMMENT '索引文件路径',
  `embedding_model` VARCHAR(100) COMMENT '使用的嵌入模型',
  `total_vectors` INT DEFAULT 0,
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_video` (`video_id`),
  CONSTRAINT `fk_vector_video` FOREIGN KEY (`video_id`) REFERENCES `videos` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='视频向量索引表'; 