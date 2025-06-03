<template>
  <v-container fluid class="pa-4 all-courses-container">
    <v-card class="content-card">
      <v-card-title class="d-flex align-center py-4 px-6">
        <v-icon class="mr-2" color="info">mdi-book-multiple</v-icon>
        所有课程
        <v-spacer></v-spacer>
        <v-text-field
          v-model="searchQuery"
          prepend-inner-icon="mdi-magnify"
          label="搜索课程..."
          single-line
          hide-details
          density="compact"
          variant="outlined"
          class="search-field"
          style="max-width: 300px"
          @input="filterCourses"
        ></v-text-field>
        <v-progress-circular
          v-if="loading"
          indeterminate
          color="primary"
          size="24"
          class="ml-4"
        ></v-progress-circular>
      </v-card-title>
      <v-divider></v-divider>
      <v-card-text class="pa-6">
        <v-row v-if="!loading && filteredCourses.length > 0">
          <v-col
            v-for="course in filteredCourses"
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
        </v-row>
        
        <v-row v-else-if="!loading && filteredCourses.length === 0 && searchQuery" class="fill-height align-center justify-center">
          <v-col cols="12" class="text-center">
            <v-icon size="64" color="grey">mdi-magnify</v-icon>
            <div class="text-h6 mt-4 text-grey">未找到相关课程</div>
            <div class="text-body-1 mt-2 text-grey">
              试试其他关键词或清空搜索条件
            </div>
            <v-btn
              color="primary"
              class="mt-4"
              @click="searchQuery = ''"
            >
              清空搜索
            </v-btn>
          </v-col>
        </v-row>
        
        <v-row v-else-if="!loading && allCourses.length === 0" class="fill-height align-center justify-center">
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

        <v-row v-else-if="loading" class="fill-height align-center justify-center">
          <v-col cols="12" class="text-center">
            <v-progress-circular
              indeterminate
              color="primary"
              size="64"
            ></v-progress-circular>
            <div class="text-h6 mt-4 text-grey">正在加载课程...</div>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import CourseCard from '../components/CourseCard.vue'
import courseService from '../api/courseService'
import { processCourseImageUrl } from '../utils/imageUtils'

interface Course {
  id: string
  thumbnail: string
  title: string
  duration: string
  students: number
  teacher: string
  category: string
}

const loading = ref(true)
const error = ref<string | null>(null)
const allCourses = ref<Course[]>([])
const searchQuery = ref('')

// 检查用户是否已登录
const isLoggedIn = computed(() => {
  return !!localStorage.getItem('wendao_token')
})

// 过滤课程
const filteredCourses = computed(() => {
  if (!searchQuery.value) {
    return allCourses.value
  }
  
  const query = searchQuery.value.toLowerCase()
  return allCourses.value.filter(course => 
    course.title.toLowerCase().includes(query) ||
    course.teacher.toLowerCase().includes(query) ||
    course.category.toLowerCase().includes(query)
  )
})

// 加载所有课程数据
const fetchAllCourses = async () => {
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
      allCourses.value = response.data.data.list.map((course: any) => {
        return {
          id: course.id,
          thumbnail: processCourseImageUrl(course.id, course.imageUrl),
          title: course.name,
          duration: `${course.hours}课时`,
          students: course.studentCount || 0,
          teacher: course.teacherInfo?.name || '未知教师',
          category: course.category || '未分类'
        };
      });
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

// 过滤课程方法
const filterCourses = () => {
  // 触发计算属性重新计算
}

onMounted(() => {
  fetchAllCourses()
})
</script>

<style scoped>
.all-courses-container {
  width: 100%;
  transition: width 0.3s ease;
  height: 100%;
  overflow-y: auto;
}

.content-card {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  overflow: visible;
}

.search-field {
  max-width: 300px;
}
</style>