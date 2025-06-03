<template>
    <v-container fluid class="pa-4">
      <v-card class="content-card">
        <v-card-title class="d-flex align-center py-4 px-6">
          个性化推荐
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
          <!-- 兴趣标签选择 -->
          
  
          <!-- 推荐课程列表 -->
          <v-card class="mb-6">
            <v-card-title class="py-3 px-6">
              <v-icon start color="info" class="mr-2">mdi-star</v-icon>
              推荐课程
              <v-spacer></v-spacer>
              <v-progress-circular
                v-if="loading"
                indeterminate
                color="primary"
                size="24"
              ></v-progress-circular>
            </v-card-title>
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
  
          <!-- 学习路径推荐 -->
          <v-card>
            <v-card-title class="py-3 px-6">
              <v-icon start color="primary" class="mr-2">mdi-map-marker-path</v-icon>
              成长路径
            </v-card-title>
            <v-card-text>
              <v-timeline v-if="learningPaths.length > 0">
                <v-timeline-item
                  v-for="path in learningPaths"
                  :key="path.id"
                  :dot-color="path.color"
                  size="small"
                >
                  <template v-slot:opposite>
                    <div class="text-caption">{{ path.duration }}</div>
                  </template>
                  
                  <!-- 右侧内容（竖线右边） -->
                  <div class="d-flex flex-column">
                    <div class="text-subtitle-1 font-weight-medium">{{ path.title }}</div>
                    <div class="text-body-2 text-medium-emphasis">{{ path.description }}</div>
                  </div>
                </v-timeline-item>
              </v-timeline>
            </v-card-text>
          </v-card>
        </v-card-text>
      </v-card>
    </v-container>
  </template>
  
  <script setup lang="ts">
  import { ref, onMounted, watch, computed } from 'vue'
  import { useRouter } from 'vue-router'
  import CourseCard from '../components/CourseCard.vue'
  import courseService from '../api/courseService'
  import { processCourseImageUrl } from '../utils/imageUtils'
  import { useCourseStore } from '../stores/courseStore'
  
  
  interface LearningPath {
    id: number
    title: string
    description: string
    duration: string
    color: string
  }
  
  const router = useRouter()
  const courseStore = useCourseStore()
  const loading = ref(true)
  const error = ref<string | null>(null)
  
  // 添加类型声明
  const learningPaths = ref<LearningPath[]>([])
  
  
  // 检查用户是否已登录
  const isLoggedIn = computed(() => {
    return !!localStorage.getItem('wendao_token')
  })
  
  // 导航到所有课程页面
  const navigateToAllCourses = () => {
    router.push('/all-courses')
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
            rating: 4.5,
            teacher: course.teacherInfo?.name || '未知教师',
            category: course.category || '未分类'
          };
        });
        courseStore.setCourses(courseList)
      } else {
        error.value = response.data.message || '获取课程失败'
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
  
  onMounted(() => {
    fetchCourses()
    loadRecommendations()
  })
  
  // 模拟加载推荐数据
  const loadRecommendations = async () => {
    loading.value = true
    try {
      // 模拟API请求延迟
      await new Promise(resolve => setTimeout(resolve, 1500))
      
      // 模拟学习路径数据
      learningPaths.value = [
        {
          id: 1,
          title: '前端开发工程师',
          description: 'HTML、CSS、JavaScript基础到Vue.js框架应用',
          duration: '3个月',
          color: 'primary'
        },
        {
          id: 2,
          title: '全栈开发工程师',
          description: '前端基础、Node.js后端开发、数据库设计',
          duration: '6个月',
          color: 'success'
        },
        {
          id: 3,
          title: '数据分析师',
          description: 'Python编程、数据分析、机器学习',
          duration: '1年',
          color: 'info'
        },
        {
          id: 4,
          title: '人工智能工程师',
          description: '深度学习、自然语言处理、计算机视觉',
          duration: '3年',
          color: 'warning'
        }
      ]
    } catch (error) {
      console.error('加载推荐失败:', error)
    } finally {
      loading.value = false
    }
  }
  </script>
  
  <style scoped>
  .content-card {
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  }
  
  /* 自定义标签样式 */
  :deep(.v-chip) {
    margin: 4px;
  }
  
  :deep(.v-chip--selected) {
    background-color: #6f23d1 !important;
    color: white !important;
  }
  
 .text-body-2{
    margin: auto;
  }
 
  .text-subtitle-1{
    margin: auto;
  }
  
  /* 添加新的样式 */
  .all-courses-placeholder {
    cursor: pointer;
    transition: all 0.3s ease;
    border: 2px dashed #e0e0e0;
    background: linear-gradient(135deg, #f5f5f5, #fafafa);
  }
  
  .all-courses-placeholder:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
    border-color: #1976d2;
    background: linear-gradient(135deg, #e3f2fd, #f3e5f5);
  }
  
  .course-card {
    border-radius: 12px;
    transition: all 0.3s ease;
  }
  
  .course-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
  }
  </style>