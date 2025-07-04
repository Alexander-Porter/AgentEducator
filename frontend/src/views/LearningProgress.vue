<template>
  <div class="learning-progress">
    <v-container fluid class="pa-4">
      <v-card class="content-card">
        <v-card-title class="d-flex align-center py-4 px-6">
          学习进度
          <v-spacer></v-spacer>
          <v-text-field
            v-model="search"
            prepend-inner-icon="mdi-magnify"
            label="搜索课程"
            single-line
            hide-details
            density="compact"
            variant="outlined"
            class="search-field"
            style="max-width: 300px"
          ></v-text-field>
        </v-card-title>
        <v-divider></v-divider>        <v-card-text class="pa-4">
          <!-- 加载状态 -->
          <div v-if="loading" class="text-center py-8">
            <v-progress-circular indeterminate color="primary"></v-progress-circular>
            <div class="mt-2 text-grey">正在加载学习进度...</div>
          </div>

          <!-- 错误状态 -->
          <v-alert v-else-if="error" type="error" class="mb-4">
            {{ error }}
            <template v-slot:append>
              <v-btn variant="text" @click="fetchLearningProgress">重试</v-btn>
            </template>
          </v-alert>

          <!-- 成功加载数据 -->
          <template v-else>
            <!-- 将统计卡片改成瀑布流布局 -->
            <v-row dense class="stats-flow">
              <v-col cols="6" sm="3" class="stat-col">
                <v-card class="stat-card" elevation="1" hover>
                  <v-card-text class="stat-card-content">
                    <div class="d-flex align-center">
                      <div class="stat-icon purple me-3">
                        <v-icon>mdi-book-open-page-variant</v-icon>
                      </div>
                      <div>
                        <div class="text-h5">{{ stats.activeCourses }}</div>
                        <div class="text-caption text-medium-emphasis">在学课程</div>
                      </div>
                    </div>
                  </v-card-text>
                </v-card>
              </v-col>

              <v-col cols="6" sm="3" class="stat-col">
                <v-card class="stat-card" elevation="1" hover>
                  <v-card-text class="stat-card-content">
                    <div class="d-flex align-center">
                      <div class="stat-icon blue me-3">
                        <v-icon>mdi-clock-outline</v-icon>
                      </div>
                      <div>
                        <div class="text-h5">{{ stats.studyHours }}</div>
                        <div class="text-caption text-medium-emphasis">学习时长(小时)</div>
                      </div>
                    </div>
                  </v-card-text>
                </v-card>
              </v-col>

              <v-col cols="6" sm="3" class="stat-col">
                <v-card class="stat-card" elevation="1" hover>
                  <v-card-text class="stat-card-content">
                    <div class="d-flex align-center">
                      <div class="stat-icon green me-3">
                        <v-icon>mdi-certificate-outline</v-icon>
                      </div>
                      <div>
                        <div class="text-h5">{{ stats.certificates }}</div>
                        <div class="text-caption text-medium-emphasis">已获证书</div>
                      </div>
                    </div>
                  </v-card-text>
                </v-card>
              </v-col>

              <v-col cols="6" sm="3" class="stat-col">
                <v-card class="stat-card" elevation="1" hover>
                  <v-card-text class="stat-card-content">
                    <div class="d-flex align-center">
                      <div class="stat-icon orange me-3">
                        <v-icon>mdi-star-outline</v-icon>
                      </div>
                      <div>
                        <div class="text-h5">{{ stats.avgRating }}</div>
                        <div class="text-caption text-medium-emphasis">平均评分*</div>
                      </div>
                    </div>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>

            <!-- 数据说明 -->
            <v-alert type="info" density="compact" class="mb-4" variant="tonal">
              <v-icon start>mdi-information-outline</v-icon>
              <span class="text-caption">
                * 平均评分为模拟数据，评分系统正在开发中。
                证书只有在完成课程所有视频后才会获得。
              </span>
            </v-alert>
          </template>          <!-- 课程进度列表 -->
          <v-card v-if="!loading && !error" class="mb-4">
            <v-card-title class="d-flex align-center py-4 px-6">
              当前学习进度
              <v-spacer></v-spacer>
              <v-chip v-if="filteredCourses.length > 0" size="small" color="primary" variant="tonal">
                {{ filteredCourses.length }} 门课程
              </v-chip>
            </v-card-title>
            <v-divider></v-divider>
            <v-card-text class="pa-6">
              <!-- 无课程数据时的提示 -->
              <div v-if="filteredCourses.length === 0" class="text-center py-8">
                <v-icon size="64" color="grey-lighten-1" class="mb-4">mdi-book-open-outline</v-icon>
                <div class="text-h6 text-grey mb-2">
                  {{ search ? '没有找到匹配的课程' : '还没有开始学习任何课程' }}
                </div>
                <div class="text-body-2 text-grey-darken-1 mb-4">
                  {{ search ? '尝试调整搜索关键词' : '开始学习第一门课程，开启你的学习之旅吧！' }}
                </div>
                <v-btn v-if="!search" color="primary" variant="elevated" @click="router.push('/courses')">
                  浏览课程
                </v-btn>
              </div>

              <!-- 课程列表 -->
              <v-list v-else>
                <v-list-item v-for="course in filteredCourses" :key="course.id" class="mb-4">
                  <template v-slot:prepend>
                    <v-avatar size="48" color="grey-lighten-2">
                      <v-img v-if="course.image" :src="course.image" cover></v-img>
                      <v-icon v-else>mdi-book-open-variant</v-icon>
                    </v-avatar>
                  </template>
                  <v-list-item-title class="text-h6 mb-1">{{ course.name }}</v-list-item-title>
                  <v-list-item-subtitle>
                    <div class="progress-info d-flex align-center justify-space-between mb-2">
                      <span class="text-body-2">已完成 {{ course.completedLessons }}/{{ course.totalLessons }} 课时</span>
                      <span class="text-primary font-weight-bold">{{ course.progress }}%</span>
                    </div>
                    <v-progress-linear
                      :model-value="course.progress"
                      height="8"
                      rounded
                      :color="course.progress >= 80 ? 'success' : 'primary'"
                      bg-color="primary-lighten-4"
                    ></v-progress-linear>
                    <div class="course-meta d-flex align-center mt-2">
                      <v-chip size="small" class="mr-2" color="primary-lighten-4">
                        <v-icon start size="16">mdi-clock-outline</v-icon>
                        {{ course.lastStudyTime }}
                      </v-chip>
                      <v-chip size="small" :color="course.remainingDays <= 7 ? 'error' : 'warning'">
                        <v-icon start size="16">mdi-calendar</v-icon>
                        剩余 {{ course.remainingDays }} 天
                      </v-chip>
                      <v-spacer></v-spacer>
                      <v-btn
                        color="primary"
                        variant="text"
                        @click="continueLearning(course.id)"
                      >
                        继续学习
                        <v-icon end>mdi-arrow-right</v-icon>
                      </v-btn>
                    </div>
                  </v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </v-card-text>
          </v-card>          <!-- 学习趋势和待办任务 -->
          <v-row v-if="!loading && !error">
            <v-col cols="12" md="8">
              <v-card>
                <v-card-title class="py-4 px-6">学习趋势</v-card-title>
                <v-divider></v-divider>
                <v-card-text class="pa-6">
                  <div class="chart-container" style="height: 300px">
                    <!-- 这里可以集成图表库，如 ECharts -->
                    <div class="d-flex align-center justify-center fill-height text-grey">
                      <div class="text-center">
                        <v-icon size="48" class="mb-2">mdi-chart-line</v-icon>
                        <div class="text-h6 mb-2">学习趋势图表</div>
                        <div class="text-body-2">功能开发中，敬请期待</div>
                      </div>
                    </div>
                  </div>
                </v-card-text>
              </v-card>
            </v-col>

            <v-col cols="12" md="4">
              <v-card>
                <v-card-title class="py-4 px-6">
                  待完成任务
                  <v-chip size="small" color="info" variant="tonal" class="ml-2">模拟数据</v-chip>
                </v-card-title>
                <v-divider></v-divider>
                <v-card-text class="pa-6">
                  <!-- 待办任务说明 -->
                  <v-alert type="info" density="compact" class="mb-4" variant="tonal">
                    <v-icon start size="16">mdi-information-outline</v-icon>
                    <span class="text-caption">任务系统正在开发中，当前显示为模拟数据</span>
                  </v-alert>
                  
                  <v-list>
                    <v-list-item v-for="task in tasks" :key="task.id">
                      <template v-slot:prepend>
                        <v-checkbox-btn v-model="task.completed"></v-checkbox-btn>
                      </template>
                      <v-list-item-title :class="{ 'text-decoration-line-through': task.completed }">
                        {{ task.title }}
                      </v-list-item-title>
                      <v-list-item-subtitle class="mt-1">
                        <v-chip
                          size="x-small"
                          :color="task.priority === 'high' ? 'error' : 'warning'"
                          text-color="white"
                        >
                          {{ task.priority === 'high' ? '紧急' : '普通' }}
                        </v-chip>
                        <span class="ml-2 text-grey">{{ task.dueDate }}</span>
                      </v-list-item-subtitle>
                    </v-list-item>
                  </v-list>
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>
    </v-container>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import courseService from '../api/courseService'

const router = useRouter()
const search = ref('')
const loading = ref(true)
const error = ref<string | null>(null)

// 统计数据
const stats = ref({
  activeCourses: 0,
  studyHours: 0,
  certificates: 0,
  avgRating: 4.8
})

// 课程进度数据
const courses = ref<any[]>([])

// 待办任务 - 暂时使用模拟数据，因为后端还没有任务系统
const tasks = ref([
  {
    id: 1,
    title: '软件工程第四章作业',
    priority: 'high',
    dueDate: '今天截止',
    completed: false
  },
  {
    id: 2,
    title: '计算机网络实验报告',
    priority: 'normal',
    dueDate: '还剩3天',
    completed: false
  },
  {
    id: 3,
    title: '算法设计课后习题',
    priority: 'normal',
    dueDate: '还剩5天',
    completed: false
  }
])

// 过滤课程（基于搜索）
const filteredCourses = computed(() => {
  if (!search.value) {
    return courses.value
  }
  
  const query = search.value.toLowerCase()
  return courses.value.filter(course => 
    course.name.toLowerCase().includes(query)
  )
})

// 获取学习进度数据
const fetchLearningProgress = async () => {
  try {
    loading.value = true
    error.value = null
    
    const response = await courseService.getLearningProgress()
    
    if (response.data.code === 200) {
      const data = response.data.data
      stats.value = data.stats
      courses.value = data.courses
    } else {
      error.value = response.data.message || '获取学习进度失败'
      console.error(error.value)
    }
  } catch (err: unknown) {
    const errorObj = err as Error
    error.value = errorObj.message || '获取学习进度出错'
    console.error('获取学习进度失败:', errorObj)
  } finally {
    loading.value = false
  }
}

const continueLearning = (courseId: string) => {
  router.push(`/course/${courseId}`)
}

onMounted(() => {
  fetchLearningProgress()
})
</script>

<style scoped>
.learning-progress {
  width: 100%;
  height: 100%;
  overflow-y: auto;
}

.content-card {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  overflow: visible;
}

/* 瀑布流统计卡片样式 */
.stats-flow {
  margin-bottom: 20px;
}

.stat-col {
  padding: 4px;
}

.stat-card {
  transition: all 0.2s;
  border-radius: 8px;
  height: 100%;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.1) !important;
}

.stat-card-content {
  padding: 12px !important;
}

.stat-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-icon.purple {
  background-color: #6f23d1;
  color: white;
}

.stat-icon.blue {
  background-color: #3498db;
  color: white;
}

.stat-icon.green {
  background-color: #2ecc71;
  color: white;
}

.stat-icon.orange {
  background-color: #f39c12;
  color: white;
}

/* 确保卡片高度自适应 */
.text-h5 {
  line-height: 1.2;
  margin-bottom: 2px;
  font-weight: 600;
}

.search-field {
  max-width: 300px;
}

:deep(.v-card) {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  overflow: visible;
}

/* 确保课程列表能够滚动 */
:deep(.v-card-text) {
  max-height: none;
  overflow-y: visible;
}

/* 针对课程卡片外层容器的滚动设置 */
:deep(.v-list) {
  max-height: 400px;
  overflow-y: auto;
  padding: 0;
}
</style>