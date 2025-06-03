<template>
  <v-container fluid class="pa-4 home-container">    <!-- 从上次中断的地方继续 - 条状物设计 -->
    <v-card v-if="isLoggedIn && homepageData.recentVideos && homepageData.recentVideos.length > 0" class="content-card mb-4">
      <v-card-title class="d-flex align-center py-4 px-6">
        <v-icon class="mr-2" color="warning">mdi-restore</v-icon>
        从上次中断的地方继续
      </v-card-title>
      <v-divider></v-divider>
      <v-card-text class="pa-4">
        <div class="continue-learning-list">
          <div
            v-for="video in homepageData.recentVideos"
            :key="video.videoId"
            class="continue-learning-item"
            @click="navigateToVideo(video)"
          >
            <div class="video-thumbnail">
              <v-img
                :src="video.coverUrl || '/default-video.jpg'"
                width="120"
                height="68"
                cover
                class="rounded"
              >
                <div class="play-overlay">
                  <v-icon color="white" size="24">mdi-play-circle</v-icon>
                </div>
              </v-img>
            </div>
            <div class="video-info">
              <div class="video-title">{{ video.title }}</div>
              <div class="video-course">{{ video.courseName }}</div>
              <div class="video-progress-info">
                <span class="progress-text">{{ video.progressPercent }}% 完成</span>
                <span class="duration-text">{{ video.durationFormatted }}</span>
              </div>
              <v-progress-linear
                :model-value="video.progressPercent"
                color="warning"
                height="3"
                class="mt-2"
                rounded
              ></v-progress-linear>
            </div>
            <div class="continue-action">
              <v-btn
                color="warning"
                variant="flat"
                size="small"
                @click.stop="navigateToVideo(video)"
              >
                继续观看
              </v-btn>
            </div>
          </div>
        </div>
      </v-card-text>
    </v-card>

    <!-- 大家都在学 -->
    <v-card v-if="homepageData.popularCourses && homepageData.popularCourses.length > 0" class="content-card mb-4">
      <v-card-title class="d-flex align-center py-4 px-6">
        <v-icon class="mr-2" color="primary">mdi-trending-up</v-icon>
        大家都在学
        <v-spacer></v-spacer>
        <v-progress-circular
          v-if="loading"
          indeterminate
          color="primary"
          size="24"
        ></v-progress-circular>
      </v-card-title>
      <v-divider></v-divider>
      <v-card-text class="pa-6">
        <v-row>
          <v-col
            v-for="course in homepageData.popularCourses"
            :key="course.id"
            cols="12"
            sm="6"
            md="4"
            lg="3"
          >
            <v-card class="course-card" elevation="2" hover>
              <v-img
                :src="course.imageUrl || '/default-course.jpg'"
                height="150"
                cover
              >
                <div class="course-overlay">
                  <v-chip size="small" color="primary" class="ma-2">
                    {{ course.learnerCount }}人在学
                  </v-chip>
                </div>
              </v-img>
              <v-card-text class="pa-4">
                <div class="text-h6 mb-2">{{ course.name }}</div>
                <div class="text-body-2 text-grey mb-2">{{ course.teacherInfo.name }}</div>                <div class="d-flex align-center justify-space-between">
                  <v-chip size="small" color="orange" variant="outlined">
                    <v-icon start size="16">mdi-account-group</v-icon>
                    {{ course.learnerCount }}人学习
                  </v-chip>
                  <v-btn
                    color="primary"
                    variant="text"
                    size="small"
                    :to="`/course/${course.id}`"
                  >
                    查看课程
                  </v-btn>
                </div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- 我选修的课程 - 使用CourseCard组件 -->
    <v-card v-if="isLoggedIn && homepageData.continueLearningCourses && homepageData.continueLearningCourses.length > 0" class="content-card mb-4">
      <v-card-title class="d-flex align-center py-4 px-6">
        <v-icon class="mr-2" color="success">mdi-school</v-icon>
        我选修的课程
      </v-card-title>
      <v-divider></v-divider>
      <v-card-text class="pa-6">
        <v-row>
          <v-col
            v-for="course in homepageData.continueLearningCourses"
            :key="course.id"
            cols="12"
            sm="6"
            md="4"
            lg="3"
          >
            <CourseCard
              :id="course.id"
              :thumbnail="course.imageUrl || '/default-course.jpg'"
              :title="course.name"
              :duration="`${course.hours}课时`"
              :students="course.studentCount"
              :teacher="course.teacherInfo.name"
              :category="`进度: ${course.progressPercent}%`"
            />
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- 推荐课程 -->
    <v-card class="content-card">
      <v-card-title class="d-flex align-center py-4 px-6">
        <v-icon class="mr-2" color="info">mdi-star</v-icon>
        推荐课程
        <v-spacer></v-spacer>
        <v-progress-circular
          v-if="loading"
          indeterminate
          color="primary"
          size="24"
        ></v-progress-circular>
      </v-card-title>
      <v-divider></v-divider>
      <v-card-text class="pa-6">
        <v-row v-if="!loading && courseStore.courses.length > 0">
          <v-col
            v-for="course in courseStore.courses"
            :key="course.id"
            cols="12"
            sm="6"
            md="4"
            lg="3"
            xl="2"
          >
            <CourseCard
              :id="course.id"
              :thumbnail="course.thumbnail"
              :title="course.title"
              :duration="course.duration"
              :students="course.students"
              :teacher="course.teacher"
              :category="course.category"
            />
          </v-col>
          <!-- 所有课程占位方块 -->
          <v-col cols="12" sm="6" md="4" lg="3" xl="2">
            <v-card 
              class="all-courses-placeholder" 
              elevation="2" 
              hover 
              @click="navigateToAllCourses"
            >
              <v-card-text class="d-flex flex-column align-center justify-center pa-6" style="height: 300px;">
                <v-icon size="64" color="primary" class="mb-4">mdi-view-grid-plus</v-icon>
                <div class="text-h6 text-center text-primary">查看所有课程</div>
                <div class="text-body-2 text-center text-grey mt-2">探索更多精彩内容</div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
        
        <v-row v-else-if="!loading && courseStore.courses.length === 0" class="fill-height align-center justify-center">
          <v-col cols="12" class="text-center">
            <v-icon size="64" color="grey">mdi-book-off</v-icon>
            <div class="text-h6 mt-4 text-grey">暂无可访问的课程</div>
            <div class="text-body-1 mt-2 text-grey">
              {{ isLoggedIn ? '可能需要教师授予访问权限' : '请登录以查看更多课程' }}
            </div>
            <v-btn
              v-if="!isLoggedIn"
              color="primary"
              class="mt-4"
              to="/login"
            >
              去登录
            </v-btn>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import CourseCard from '../components/CourseCard.vue'
import courseService from '../api/courseService'
import userService from '../api/userService'
import { processCourseImageUrl } from '../utils/imageUtils'
import { useCourseStore } from '../stores/courseStore'
import type { AxiosResponse } from 'axios'

// 定义接口
interface MenuItem {
  title: string
  icon: string
  path: string
}

interface Course {
  id: string
  thumbnail: string
  title: string
  duration: string
  students: number
  teacher: string
  category: string
}

interface ApiResponse<T> {
  code: number
  message: string
  data: {
    list: T[]
  }
}

interface PopularCourse {
  id: string
  name: string
  code: string
  imageUrl: string
  hours: number
  studentCount: number
  teacherInfo: {
    id: number
    name: string
  }
  totalWatchTime: number
  learnerCount: number
  category: string
}

interface ContinueLearningCourse {
  id: string
  name: string
  code: string
  imageUrl: string
  hours: number
  studentCount: number
  teacherInfo: {
    id: number
    name: string
  }
  userWatchTime: number
  watchedVideos: number
  lastStudyTime: string | null
  progressPercent: number
  category: string
}

interface RecentVideo {
  videoId: string
  courseId: string
  title: string
  courseName: string
  coverUrl: string
  duration: number
  durationFormatted: string
  lastPosition: number
  lastPositionFormatted: string
  progressPercent: number
  lastWatchTime: string | null
  watchUrl: string
}

interface HomepageData {
  popularCourses: PopularCourse[]
  continueLearningCourses: ContinueLearningCourse[]
  recentVideos: RecentVideo[]
}

const router = useRouter()
const route = useRoute()
const courseStore = useCourseStore()
const loading = ref(true)
const error = ref<string | null>(null)
const homepageData = ref<HomepageData>({
  popularCourses: [],
  continueLearningCourses: [],
  recentVideos: []
})

const menuItems: MenuItem[] = [
  { title: '推荐课程', icon: 'mdi-book-open-variant', path: '/' },
  { title: '学习进度', icon: 'mdi-progress-check', path: '/learning-progress' },
  { title: '笔记本', icon: 'mdi-notebook', path: '/notebook' },
  { title: 'AI助手', icon: 'mdi-robot', path: '/ai-assistant' }
]

// 添加路由导航方法
const navigateToPage = (path: string) => {
  router.push(path)
}

// 导航到所有课程页面
const navigateToAllCourses = () => {
  router.push('/all-courses')
}

// 导航到视频播放页面
const navigateToVideo = (video: RecentVideo) => {
  router.push(`/course/${video.courseId}/video/${video.videoId}`)
}

// 检查用户是否已登录
const isLoggedIn = computed(() => {
  return !!localStorage.getItem('wendao_token')
})

// 格式化最后观看时间
const formatLastWatchTime = (lastWatchTime: string | null): string => {
  if (!lastWatchTime) return '未知时间'
  
  const now = new Date()
  const watchTime = new Date(lastWatchTime)
  const diffInSeconds = Math.floor((now.getTime() - watchTime.getTime()) / 1000)
  
  if (diffInSeconds < 60) return '刚刚'
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}分钟前`
  if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}小时前`
  if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)}天前`
  
  return watchTime.toLocaleDateString()
}

// 加载首页数据
const fetchHomepageData = async () => {
  try {
    loading.value = true
    error.value = null
    
    const response = await courseService.getHomepageData()
    
    if (response.data.code === 200) {
      homepageData.value = response.data.data
    } else {
      error.value = response.data.message || '获取首页数据失败'
      console.error(error.value)
    }
  } catch (err: unknown) {
    const errorObj = err as Error
    error.value = errorObj.message || '获取首页数据出错'
    console.error('获取首页数据失败:', errorObj)
  } finally {
    loading.value = false
  }
}

// 加载课程数据
const fetchCourses = async () => {
  try {
    loading.value = true
    error.value = null
    
    // 根据登录状态获取不同的课程列表
    let response;
    if (isLoggedIn.value) {
      response = await courseService.getStudentCourses()
    } else {
      response = await courseService.getStudentCourses({ public: true })
    }
    
    if (response.data.code === 200) {
      // 处理课程数据，修复图片路径
      const courseList = response.data.data.list.map((course: any) => {
        return {
          id: course.id,
          thumbnail: processCourseImageUrl(course.id, course.imageUrl),
          title: course.name,
          duration: `${course.hours}课时`,
          students: course.studentCount || 0,
          rating: 4.5, // 暂时使用固定值，等后续有评分系统再改
          teacher: course.teacherInfo?.name || '未知教师',
          category: course.category || '未分类'
        };
      });
      courseStore.setCourses(courseList) // 只同步到全局 store
    } else {
      error.value = response.data.data.message || '获取课程失败'
      console.error(error.value)
    }
  } catch (err: unknown) {
    const errorObj = err as Error
    error.value = errorObj.message || '获取课程出错'
    console.error('获取课程列表失败:', errorObj)
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  // 并行加载首页数据和推荐课程
  await Promise.all([
    fetchHomepageData(),
    fetchCourses()
  ])
})
</script>

<style scoped>
/* 主页容器 */
.home-container {
  background: transparent;
  min-height: 100%;
}

/* 内容卡片 */
.content-card {
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  background: rgba(255, 255, 255, 0.8);
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.1),
    0 2px 8px rgba(0, 0, 0, 0.05);
  transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  margin-bottom: 24px;
  overflow: hidden;
  position: relative;
}

.content-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg, #667eea, #764ba2, #f093fb);
  opacity: 0.8;
}

.content-card:hover {
  transform: translateY(-2px);
  box-shadow: 
    0 12px 48px rgba(0, 0, 0, 0.15),
    0 4px 16px rgba(0, 0, 0, 0.1);
}

/* 卡片标题区域 */
:deep(.content-card .v-card-title) {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.05), rgba(118, 75, 162, 0.03));
  border-bottom: 1px solid rgba(102, 126, 234, 0.1);
  font-weight: 700;
  color: #2d3748;
  letter-spacing: 0.5px;
}

:deep(.content-card .v-card-title .v-icon) {
  margin-right: 12px;
  opacity: 0.8;
}

/* 继续学习项目 */
.continue-learning-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.continue-learning-item {
  display: flex;
  align-items: center;
  padding: 16px;
  background: rgba(255, 255, 255, 0.6);
  border-radius: 12px;
  border: 1px solid rgba(102, 126, 234, 0.1);
  transition: all 0.3s ease;
  cursor: pointer;
}

.continue-learning-item:hover {
  background: rgba(255, 255, 255, 0.9);
  transform: translateX(4px);
  border-color: rgba(102, 126, 234, 0.2);
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.15);
}

.video-thumbnail {
  position: relative;
  margin-right: 16px;
  border-radius: 8px;
  overflow: hidden;
}

.play-overlay {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: rgba(0, 0, 0, 0.3);
  border-radius: 50%;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.continue-learning-item:hover .play-overlay {
  background: rgba(102, 126, 234, 0.8);
  transform: translate(-50%, -50%) scale(1.1);
}

.video-info {
  flex: 1;
}

.video-title {
  font-weight: 600;
  font-size: 16px;
  color: #2d3748;
  margin-bottom: 4px;
}

.video-course {
  font-size: 14px;
  color: #64748b;
  margin-bottom: 8px;
}

.video-progress-info {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #94a3b8;
  margin-bottom: 4px;
}

.continue-action {
  margin-left: 16px;
}

/* 课程卡片优化 */
.course-card {
  border-radius: 12px;
  transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  border: 1px solid rgba(102, 126, 234, 0.1);
  overflow: hidden;
}

.course-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(102, 126, 234, 0.2);
  border-color: rgba(102, 126, 234, 0.2);
}

.course-overlay {
  position: absolute;
  top: 0;
  right: 0;
}

/* "查看所有课程"占位卡片 */
.all-courses-placeholder {
  border: 2px dashed rgba(102, 126, 234, 0.3);
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.05), rgba(118, 75, 162, 0.03));
  transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  cursor: pointer;
}

.all-courses-placeholder:hover {
  border-color: rgba(102, 126, 234, 0.5);
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.05));
  transform: translateY(-4px);
}

/* 加载动画 */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.content-card {
  animation: fadeInUp 0.6s ease-out;
}

.content-card:nth-child(1) { animation-delay: 0.1s; }
.content-card:nth-child(2) { animation-delay: 0.2s; }
.content-card:nth-child(3) { animation-delay: 0.3s; }

/* 响应式设计 */
@media (max-width: 768px) {
  .continue-learning-item {
    flex-direction: column;
    text-align: center;
  }
  
  .video-thumbnail {
    margin-right: 0;
    margin-bottom: 12px;
  }
  
  .continue-action {
    margin-left: 0;
    margin-top: 12px;
  }
}
</style>