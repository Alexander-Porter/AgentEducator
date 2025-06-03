<template>
  <div class="videos-upload">
    <v-container fluid class="pa-4">
      <v-card class="content-card">
        <v-card-title class="d-flex align-center py-4 px-6">
          视频上传
          <v-spacer></v-spacer>
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text class="pa-6">
          <!-- 上传区域 -->
          <div class="upload-section">
            <!-- 课程选择框 -->
            <div class="course-selector mb-4">
              <v-select
                v-model="selectedCourseId"
                :items="courses"
                item-title="name"
                item-value="id"
                label="选择关联课程"
                variant="outlined"
                density="compact"
              ></v-select>
            </div>

            <!-- 文件选择 -->
            <v-file-input
              v-model="allFiles"
              multiple
              label="选择视频文件和字幕文件"
              variant="outlined"
              density="compact"
              accept="video/*,.json"
              class="mb-4"
            ></v-file-input>
            
            <!-- 显示匹配结果 -->
            <div v-if="allFiles.length" class="selected-files mb-4">
              <v-card variant="outlined" class="pa-3">
                <v-card-subtitle>文件匹配情况</v-card-subtitle>
                <div v-for="match in fileMatches" :key="match.video.name" class="mb-2">
                  <div class="d-flex align-center">
                    <v-icon color="primary" class="mr-2">mdi-video</v-icon>
                    <span class="text-body-2">{{ match.video.name }}</span>
                  </div>
                  <div v-if="match.subtitle" class="d-flex align-center ml-6">
                    <v-icon color="success" class="mr-2">mdi-subtitles</v-icon>
                    <span class="text-body-2 text-success">{{ match.subtitle.name }}</span>
                  </div>
                  <div v-else class="d-flex align-center ml-6">
                    <v-icon color="warning" class="mr-2">mdi-alert</v-icon>
                    <span class="text-body-2 text-warning">未找到匹配的字幕文件</span>
                  </div>
                </div>
              </v-card>
            </div>

            <!-- 上传进度条 -->
            <div v-if="uploading" class="upload-progress mb-4">
              <div class="d-flex justify-space-between align-center mb-2">
                <span class="text-body-2">上传进度</span>
                <span class="text-body-2">{{ uploadProgress }}%</span>
              </div>
              <v-progress-linear
                v-model="uploadProgress"
                height="8"
                rounded
                color="primary"
              ></v-progress-linear>
            </div>

            <!-- 上传按钮 -->
            <div class="upload-actions">
              <v-btn
                color="primary"
                size="large"
                :loading="uploading"
                :disabled="!allFiles.length || !selectedCourseId"
                @click="uploadVideos"
              >
                <v-icon start>mdi-cloud-upload</v-icon>
                上传视频
              </v-btn>
            </div>
          </div>
        </v-card-text>
      </v-card>
    </v-container>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue';
import { useRoute } from 'vue-router';
import courseService from '../../api/courseService';
import uploadService from '../../api/uploadService';

export default {
  name: 'VideosUpload',
  setup() {
    const route = useRoute();
    const courses = ref([]);
    const selectedCourseId = ref(null);
    const allFiles = ref([]);
    const uploading = ref(false);
    const uploadProgress = ref(0);

    const fetchCourses = async () => {
      try {
        const response = await courseService.getCourses();
        if (response.data && response.data.code === 200) {
          courses.value = response.data.data.list || [];
          
          // 如果URL中有courseId参数，自动选择对应课程
          const courseIdFromQuery = route.query.courseId;
          if (courseIdFromQuery) {
            selectedCourseId.value = courseIdFromQuery;
          }
        }
      } catch (error) {
        console.error('获取课程列表失败:', error);
      }
    };

    // 计算文件匹配情况
    const fileMatches = computed(() => {
      const videoFiles = allFiles.value.filter(file => file.type.startsWith('video/'));
      const jsonFiles = allFiles.value.filter(file => file.name.endsWith('.json'));
      
      return videoFiles.map(videoFile => {
        // 提取视频文件名前缀（去掉扩展名）
        const videoPrefix = videoFile.name.replace(/\.(mp4|avi|mov|mkv|webm)$/i, '');
        
        // 查找匹配的字幕文件
        const matchingSubtitle = jsonFiles.find(jsonFile => {
          // 去掉字幕文件的后缀（如_ai-zh.json）
          const subtitlePrefix = jsonFile.name.replace(/_ai-zh\.json$/i, '').replace(/\.json$/i, '');
          return subtitlePrefix === videoPrefix;
        });
        
        return {
          video: videoFile,
          subtitle: matchingSubtitle || null
        };
      });
    });

    const uploadVideos = async () => {
      if (!fileMatches.value.length || !selectedCourseId.value) {
        return;
      }

      uploading.value = true;
      uploadProgress.value = 0;

      try {
        const totalFiles = fileMatches.value.length;
        let completedFiles = 0;

        // 循环上传每个视频文件及其匹配的字幕
        for (const match of fileMatches.value) {
          await uploadService.uploadVideo(
            match.video,
            selectedCourseId.value,
            match.video.name.replace(/\.[^.]*$/, ''), // 去掉最后一个点及其后面的内容作为视频标题
            '', // 清空描述
            match.subtitle, // 传递匹配的字幕文件
            (progressEvent) => {
              // 计算总体进度
              if (progressEvent.lengthComputable) {
                const currentFileProgress = (progressEvent.loaded / progressEvent.total) * 100;
                const totalProgress = ((completedFiles / totalFiles) * 100) + (currentFileProgress / totalFiles);
                uploadProgress.value = Math.round(totalProgress);
              }
            }
          );
          
          completedFiles++;
        }

        uploadProgress.value = 100;

        setTimeout(() => {
          uploading.value = false;
          // 上传成功后重置表单
          allFiles.value = [];
          uploadProgress.value = 0;
          // 显示成功消息
          alert('视频上传成功！');
        }, 1000);
      } catch (error) {
        uploading.value = false;
        console.error('视频上传失败:', error);
        alert('视频上传失败: ' + (error.message || '未知错误'));
      }
    };

    onMounted(() => {
      fetchCourses();
    });

    return {
      courses,
      selectedCourseId,
      allFiles,
      fileMatches,
      uploading,
      uploadProgress,
      uploadVideos
    };
  }
};
</script>

<style scoped>
.videos-upload {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.content-card {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.content-card > .v-card-text {
  overflow-y: auto;
  flex: 1;
}

.upload-section {
  max-width: 800px;
  margin: 0 auto;
}

.upload-actions {
  display: flex;
  justify-content: center;
  margin-top: 2rem;
}
</style>