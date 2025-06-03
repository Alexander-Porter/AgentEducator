   CREATE TABLE video_processing_tasks (
     id INT AUTO_INCREMENT PRIMARY KEY,
     video_id INT NOT NULL,
     task_id VARCHAR(100),
     status VARCHAR(20) DEFAULT 'pending',
     processing_type VARCHAR(20),
     progress FLOAT DEFAULT 0.0,
     error_message TEXT,
     start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
     end_time DATETIME,
     FOREIGN KEY (video_id) REFERENCES videos(id)
   );