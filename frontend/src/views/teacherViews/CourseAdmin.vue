<template>
  <v-container fluid class="pa-4 course-admin-container">
    <v-card class="content-card">
      <v-card-title class="d-flex align-center py-4 px-6">
        课程管理
        <v-spacer></v-spacer>
        <v-text-field
          v-model="searchQuery"
          prepend-inner-icon="mdi-magnify"
          label="搜索课程..."
          single-line
          hide-details
          density="compact"
          class="search-field"
          @input="filterCourses"
        ></v-text-field>
      </v-card-title>
      <v-divider></v-divider>
      
      <v-card-text class="pa-4">
        <!-- 操作栏 -->
        <v-row class="mb-4">
          <v-col cols="12" sm="8">
            <div class="d-flex flex-wrap align-center">
              <v-btn
                color="primary"
                prepend-icon="mdi-plus"
                class="me-3 mb-2"
                @click="showAddCourseModal"
              >
                新建课程
              </v-btn>
              
              <v-select
                v-model="statusFilter"
                :items="[
                  { title: '所有状态', value: 'all' },
                  { title: '进行中', value: 'active' },
                  { title: '即将开始', value: 'upcoming' },
                  { title: '已结束', value: 'completed' }
                ]"
                item-title="title"
                item-value="value"
                label="状态"
                density="compact"
                class="filter-select me-3 mb-2"
                hide-details
                @update:model-value="filterCourses"
              ></v-select>
              
              <v-select
                v-model="semesterFilter"
                :items="[
                  { title: '所有学期', value: 'all' },
                  { title: '2023年秋季', value: '2023-fall' },
                  { title: '2023年春季', value: '2023-spring' },
                  { title: '2022年秋季', value: '2022-fall' }
                ]"
                item-title="title"
                item-value="value"
                label="学期"
                density="compact"
                class="filter-select mb-2"
                hide-details
                @update:model-value="filterCourses"
              ></v-select>
            </div>
          </v-col>
          
          <v-col cols="12" sm="4" class="d-flex justify-end">
            <v-btn-toggle v-model="viewMode" mandatory density="comfortable">
              <v-btn icon value="grid">
                <v-icon>mdi-view-grid</v-icon>
              </v-btn>
              <v-btn icon value="list">
                <v-icon>mdi-view-list</v-icon>
              </v-btn>
            </v-btn-toggle>
          </v-col>
        </v-row>
        
        <!-- 统计卡片 -->
        <v-row class="mb-6">
          <v-col v-for="(stat, index) in statsItems" :key="index" cols="12" sm="6" md="3">
            <v-card :color="stat.color" variant="flat" class="stat-card">
              <v-card-text>
                <div class="d-flex align-center">
                  <v-icon size="32" :icon="stat.icon" class="me-3"></v-icon>
                  <div>
                    <div class="text-subtitle-2 text-medium-emphasis">{{ stat.title }}</div>
                    <div class="text-h4 font-weight-bold">{{ stat.value }}</div>
                  </div>
                </div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
        
        <!-- 网格视图 -->
        <v-row v-if="viewMode === 'grid' && filteredCourses.length > 0">
          <v-col            v-for="course in filteredCourses"
            :key="course.id?.toString() || ''"
            cols="12"
            sm="6"
            md="4"
            lg="3"
          >
            <v-card class="course-card">
              <div class="status-indicator" :class="course.status"></div>
              <v-img
                :src="course.image || 'https://picsum.photos/400/200?random=' + course.id"
                height="180"
                cover
              ></v-img>
              
              <v-card-item>
                <v-card-title class="text-h6 mb-1">{{ course.name }}</v-card-title>
                <v-card-subtitle>课程编码: {{ course.code }}</v-card-subtitle>
              </v-card-item>
              
              <v-card-text>
                <div class="d-flex mb-2">
                  <v-icon size="small" class="me-1">mdi-account-group</v-icon>
                  <span class="text-body-2 me-3">{{ course.studentCount }}人</span>
                  <v-icon size="small" class="me-1">mdi-clock-outline</v-icon>
                  <span class="text-body-2">{{ course.hours }}学时</span>
                </div>
                <div class="text-body-2 text-truncate-3">{{ course.description }}</div>
                <div class="mt-2 d-flex align-center">
                  <v-icon size="small" class="me-1">mdi-calendar</v-icon>
                  <span class="text-caption">{{ course.startDate }} ~ {{ course.endDate }}</span>
                </div>
              </v-card-text>
              
              <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn icon variant="text" @click="editCourse(course)">
                  <v-icon>mdi-pencil</v-icon>
                </v-btn>
                <v-btn icon variant="text" @click="viewCourseDetail(course)">
                  <v-icon>mdi-eye</v-icon>
                </v-btn>
                <v-btn icon variant="text" @click="manageCourseVideos(course)">
                  <v-icon>mdi-video</v-icon>
                </v-btn>
                <v-btn icon variant="text" @click="confirmDeleteCourse(course)">
                  <v-icon>mdi-delete</v-icon>
                </v-btn>
                <v-spacer></v-spacer>
              </v-card-actions>
            </v-card>
          </v-col>
        </v-row>
        
        <!-- 列表视图 -->
        <v-table
          v-if="viewMode === 'list' && filteredCourses.length > 0"
          density="comfortable"
        >
          <thead>
            <tr>
              <th>课程名称</th>
              <th>课程编号</th>
              <th>学期</th>
              <th>开始日期</th>
              <th>结束日期</th>
              <th>学生数</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="course in filteredCourses" :key="course.id?.toString() || ''">
              <td>{{ course.name }}</td>
              <td>{{ course.code }}</td>
              <td>{{ course.semester }}</td>
              <td>{{ course.startDate }}</td>
              <td>{{ course.endDate }}</td>
              <td>{{ course.studentCount }}</td>
              <td>
                <v-chip
                  :color="getStatusColor(course.status)"
                  size="small"
                  label
                >
                  {{ getStatusText(course.status) }}
                </v-chip>
              </td>
              <td>
                <v-btn icon="mdi-pencil" size="small" variant="text" @click="editCourse(course)"></v-btn>
                <v-btn icon="mdi-eye" size="small" variant="text" @click="viewCourseDetail(course)"></v-btn>
                <v-btn icon="mdi-delete" size="small" variant="text" @click="confirmDeleteCourse(course)"></v-btn>
              </td>
            </tr>
          </tbody>
        </v-table>
        
        <!-- 空状态 -->
        <v-row v-if="filteredCourses.length === 0" class="fill-height align-center justify-center">
          <v-col cols="12" class="text-center pa-12">
            <v-icon size="64" color="grey">mdi-book-off</v-icon>
            <div class="text-h6 mt-4 text-grey">暂无符合条件的课程</div>
            <div class="text-body-1 mt-2 text-grey">
              您可以点击"新建课程"按钮创建一门新课程
            </div>
            <v-btn
              color="primary"
              class="mt-4"
              @click="showAddCourseModal"
            >
              新建课程
            </v-btn>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>
    
    <!-- 新增/编辑课程对话框 -->
    <v-dialog
      v-model="showModal"
      max-width="700px"
    >
      <v-card>
        <v-card-title class="text-h5 pa-4">
          {{ isEditing ? '编辑课程' : '新建课程' }}
          <v-spacer></v-spacer>
          <v-btn icon @click="closeModal">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text class="pa-4">
          <v-form ref="form" @submit.prevent="saveCourse">
            <v-row>
              <v-col cols="12">
                <v-text-field
                  v-model="courseForm.name"
                  label="课程名称"
                  required
                  variant="outlined"
                  density="comfortable"
                ></v-text-field>
              </v-col>
              <v-col cols="12">
                <v-text-field
                  v-model="courseForm.code"
                  label="课程编号"
                  required
                  variant="outlined"
                  density="comfortable"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="courseForm.startDate"
                  label="开始日期"
                  type="date"
                  required
                  variant="outlined"
                  density="comfortable"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="courseForm.endDate"
                  label="结束日期"
                  type="date"
                  required
                  variant="outlined"
                  density="comfortable"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model.number="courseForm.hours"
                  label="学时数"
                  type="number"
                  min="1"
                  required
                  variant="outlined"
                  density="comfortable"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="6">
                <v-select
                  v-model="courseForm.semester"
                  :items="[
                    { title: '2023年秋季学期', value: '2023-fall' },
                    { title: '2023年春季学期', value: '2023-spring' },
                    { title: '2022年秋季学期', value: '2022-fall' }
                  ]"
                  item-title="title"
                  item-value="value"
                  label="学期"
                  required
                  variant="outlined"
                  density="comfortable"
                ></v-select>
              </v-col>
              <v-col cols="12">
                <v-select
                  v-model="courseForm.status"
                  :items="[
                    { title: '即将开始', value: 'upcoming' },
                    { title: '进行中', value: 'active' },
                    { title: '已结束', value: 'completed' }
                  ]"
                  item-title="title"
                  item-value="value"
                  label="课程状态"
                  variant="outlined"
                  density="comfortable"
                ></v-select>
              </v-col>
              <v-col cols="12">
                <v-file-input
                  label="课程封面图"
                  accept="image/*"
                  show-size
                  @change="handleImageInputChange"
                  variant="outlined"
                  density="comfortable"
                ></v-file-input>
                <v-img
                  v-if="courseForm.image"
                  :src="courseForm.image"
                  max-height="200"
                  contain
                  class="mt-2"
                ></v-img>
              </v-col>
              <v-col cols="12">
                <v-textarea
                  v-model="courseForm.description"
                  label="课程描述"
                  rows="4"
                  variant="outlined"
                  density="comfortable"
                ></v-textarea>
              </v-col>
              <v-col cols="12">
                <v-checkbox
                  v-model="courseForm.isPublic"
                  label="公开课程"
                  density="comfortable"
                ></v-checkbox>
              </v-col>
            </v-row>
          </v-form>
        </v-card-text>
        <v-divider></v-divider>
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn
            variant="text"
            @click="closeModal"
          >
            取消
          </v-btn>
          <v-btn
            color="primary"
            @click="saveCourse"
          >
            保存
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    
    <!-- 删除确认对话框 -->
    <v-dialog
      v-model="showDeleteModal"
      max-width="400px"
    >
      <v-card>
        <v-card-title class="text-h5 pa-4">
          确认删除
          <v-spacer></v-spacer>
          <v-btn icon @click="closeDeleteModal">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-card-text class="pa-4 text-center">
          <v-icon
            color="error"
            size="64"
            class="mb-4"
          >
            mdi-alert-circle
          </v-icon>
          <div class="text-body-1">
            您确定要删除课程 <strong>{{ courseToDelete?.name }}</strong> 吗？
          </div>
          <div class="text-caption text-error mt-2">
            此操作无法撤销，课程的所有相关数据也将被删除。
          </div>
        </v-card-text>
        <v-divider></v-divider>
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn
            variant="text"
            @click="closeDeleteModal"
          >
            取消
          </v-btn>
          <v-btn
            color="error"
            @click="deleteCourse"
          >
            删除
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import courseService from '../../api/courseService'
import uploadService from '../../api/uploadService'
import { useUserStore } from '../../stores/userStore'

// 定义接口
interface Course {
  id: string | null
  name: string
  code: string
  description: string
  image: string
  startDate: string
  endDate: string
  hours: number
  studentCount: number
  status: string
  semester: string
  isPublic: boolean // 新增是否公开属性
}

// 路由相关
const router = useRouter()
const userStore = useUserStore()

// 状态管理
const viewMode = ref('grid')
const searchQuery = ref('')
const statusFilter = ref('all')
const semesterFilter = ref('all')
const courses = ref<Course[]>([])
const filteredCourses = ref<Course[]>([])
const imageFile = ref<File | null>(null)
const showModal = ref(false)
const isEditing = ref(false)
const showDeleteModal = ref(false)
const courseToDelete = ref<Course | null>(null)

// 课程表单
const courseForm = reactive<Course>({
  id: null,
  name: '',
  code: '',
  description: '',
  image: '',
  startDate: getTodayDate(),
  endDate: '',
  hours: 40,
  studentCount: 0,
  status: 'upcoming',
  semester: '2023-fall',
  isPublic: true // 默认公开
})

// 统计信息计算属性
const statsItems = computed(() => [
  {
    title: '总课程数',
    value: courses.value.length,
    icon: 'mdi-book-multiple',
    color: 'bg-primary-lighten-4'
  },
  {
    title: '进行中',
    value: courses.value.filter(c => c.status === 'active').length,
    icon: 'mdi-play-circle',
    color: 'bg-success-lighten-4'
  },
  {
    title: '即将开始',
    value: courses.value.filter(c => c.status === 'upcoming').length,
    icon: 'mdi-clock-outline',
    color: 'bg-info-lighten-4'
  },
  {
    title: '已结束',
    value: courses.value.filter(c => c.status === 'completed').length,
    icon: 'mdi-check-circle',
    color: 'bg-grey-lighten-3'
  }
])

// 方法
function getTodayDate() {
  const today = new Date()
  const year = today.getFullYear()
  const month = String(today.getMonth() + 1).padStart(2, '0')
  const day = String(today.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

// 管理课程视频
function manageCourseVideos(course: Course) {
  if (!course.id) return
  router.push(`/CourseVideoManage/${course.id}`)
}

// 格式化时间戳为日期格式
function formatTimestampToDate(timestamp: number) {
  if (!timestamp) return '';
  const date = new Date(timestamp);
  return date.toISOString().split('T')[0]; // 返回YYYY-MM-DD格式
}

// 筛选课程
function filterCourses() {
  let filtered = [...courses.value]
  
  // 搜索筛选
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(course => 
      course.name.toLowerCase().includes(query) || 
      course.code.toLowerCase().includes(query) ||
      course.description.toLowerCase().includes(query)
    )
  }
  
  // 状态筛选
  if (statusFilter.value !== 'all') {
    filtered = filtered.filter(course => course.status === statusFilter.value)
  }
  
  // 学期筛选
  if (semesterFilter.value !== 'all') {
    filtered = filtered.filter(course => course.semester === semesterFilter.value)
  }
  
  filteredCourses.value = filtered
}

// 获取状态文本
function getStatusText(status: string) {
  const statusMap: Record<string, string> = {
    'active': '进行中',
    'upcoming': '即将开始',
    'completed': '已结束'
  }
  return statusMap[status] || status
}

// 获取状态颜色
function getStatusColor(status: string) {
  const colorMap: Record<string, string> = {
    'active': 'success',
    'upcoming': 'info',
    'completed': 'grey'
  }
  return colorMap[status] || 'primary'
}

// 打开新建课程模态框
function showAddCourseModal() {
  isEditing.value = false
  Object.assign(courseForm, {
    id: null,
    name: '',
    code: '',
    description: '',
    image: '',
    startDate: getTodayDate(),
    endDate: '',
    hours: 40,
    studentCount: 0,
    status: 'upcoming',
    semester: '2023-fall',
    isPublic: true
  })
  imageFile.value = null
  showModal.value = true
}

// 打开编辑课程模态框
function editCourse(course: Course) {
  isEditing.value = true
  Object.assign(courseForm, course)
  showModal.value = true
}

// 关闭模态框
function closeModal() {
  showModal.value = false
}

// 处理图片上传
function handleImageInputChange(event: Event) {
  const target = event.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    imageFile.value = target.files[0]
    
    // 预览图片
    const reader = new FileReader()
    reader.onload = (e) => {
      if (e.target) {
        courseForm.image = e.target.result as string
      }
    }
    reader.readAsDataURL(imageFile.value)
  }
}

// 保存课程
async function saveCourse() {
  // 表单验证
  if (!courseForm.name || !courseForm.code || !courseForm.startDate || !courseForm.endDate) {
    alert('请填写所有必填字段')
    return
  }
  
  try {    // 转换日期为时间戳
    const dateToTimestamp = (dateStr: string | null): number => {
      if (!dateStr) return 0;
      return new Date(dateStr).getTime();
    };
    
    // 构建提交数据
    const courseData = {
      name: courseForm.name,
      code: courseForm.code,
      description: courseForm.description,
      imageUrl: courseForm.image,
      startDate: dateToTimestamp(courseForm.startDate),
      endDate: dateToTimestamp(courseForm.endDate),
      hours: courseForm.hours,
      status: mapStatusToInt(courseForm.status),
      semester: courseForm.semester,
      isPublic: courseForm.isPublic // 新增
    }
    
    // 如果有选择图片文件，先上传图片
    if (imageFile.value) {
      try {
        const uploadResponse = await uploadService.uploadImage(imageFile.value)
        if (uploadResponse.data.code === 200) {
          courseData.imageUrl = uploadResponse.data.data.imageUrl
        } else {
          throw new Error(uploadResponse.data.message || '图片上传失败')
        }      } catch (uploadError: any) {
        console.error('图片上传错误:', uploadError)
        alert('图片上传失败: ' + (uploadError.message || '未知错误'))
        return
      }
    }
    
    // 发送创建/更新课程请求
    let response
    if (isEditing.value && courseForm.id) {
      response = await courseService.updateCourse(courseForm.id, courseData)
    } else {
      response = await courseService.createCourse(courseData)
    }
    
    if (response.data.code === 200) {
      alert(isEditing.value ? '课程更新成功' : '课程创建成功')
      closeModal()
      fetchCourses() // 刷新课程列表
    } else {
      throw new Error(response.data.message || (isEditing.value ? '更新课程失败' : '创建课程失败'))
    }  } catch (error: any) {
    console.error(isEditing.value ? '更新课程错误:' : '创建课程错误:', error)
    alert(error.message || '操作失败，请重试')
  }
}

// 状态转换函数
function mapStatusToInt(status: string) {
  const statusMap: Record<string, number> = {
    'upcoming': 0,   // 即将开始
    'active': 1,     // 进行中
    'completed': 2   // 已结束
  }
  return statusMap[status] ?? 0
}

// 数字状态转字符串状态
function mapIntToStatus(statusInt: number): string {
  const statusMap: Record<number, string> = {
    0: 'upcoming',    // 即将开始
    1: 'active',      // 进行中
    2: 'completed'    // 已结束
  }
  return statusMap[statusInt] ?? 'upcoming'
}

// 打开删除确认框
function confirmDeleteCourse(course: Course) {
  courseToDelete.value = course
  showDeleteModal.value = true
}

// 关闭删除确认框
function closeDeleteModal() {
  showDeleteModal.value = false
  courseToDelete.value = null
}

// 删除课程
async function deleteCourse() {
  if (!courseToDelete.value || !courseToDelete.value.id) return
  
  try {
    const response = await courseService.deleteCourse(courseToDelete.value.id)
    
    if (response.data.code === 200) {
      // 删除成功后更新本地数据
      courses.value = courses.value.filter(c => c.id !== courseToDelete.value?.id)
      filterCourses() // 重新应用筛选
      
      alert('课程删除成功')
    } else {
      throw new Error(response.data.message || '删除课程失败')
    }
  } catch (error: any) {
    console.error('删除课程错误:', error)
    alert('删除课程失败: ' + (error.message || '未知错误'))
  } finally {
    closeDeleteModal()
  }
}

// 查看课程详情
function viewCourseDetail(course: Course) {
  console.log('查看课程详情', course)
  // 这里可以跳转到课程详情页
  // router.push(`/courses/${course.id}`)
}

// 退出登录
function logout() {
  userStore.clearUserInfo()
  router.push('/login')
}

// 获取课程列表
async function fetchCourses() {
  try {
    const response = await courseService.getCourses()
    if (response.data.code === 200) {
      // 更新课程列表
      courses.value = response.data.data.list.map((course: any) => ({
        id: course.id,
        name: course.name,
        code: course.code,
        description: course.description,
        image: course.imageUrl, // 后端返回的图片URL
        // 时间戳转换为日期格式
        startDate: formatTimestampToDate(course.startDate),
        endDate: formatTimestampToDate(course.endDate),
        hours: course.hours,
        studentCount: course.studentCount || 0,
        // 将数字状态转换为字符串状态
        status: mapIntToStatus(course.status),
        semester: course.semester,
        isPublic: course.isPublic !== undefined ? course.isPublic : true // 兼容老数据
      }))
      
      // 应用过滤器重新显示课程
      filterCourses()
    } else {
      throw new Error(response.data.message || '获取课程列表失败')
    }
  } catch (error: any) {
    console.error('获取课程列表失败:', error)
    alert('获取课程列表失败: ' + (error.message || '未知错误'))
  }
}

// 组件挂载时获取数据
onMounted(() => {
  fetchCourses()
})
</script>

<style scoped>
.course-admin-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.content-card {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
}

.content-card > .v-card-text {
  overflow-y: auto;
  flex: 1;
}

.search-field {
  max-width: 300px;
}

.filter-select {
  max-width: 180px;
}

.stat-card {
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
}

.course-card {
  position: relative;
  transition: all 0.3s ease;
  height: 100%;
  overflow: hidden;
}

.course-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
}

.status-indicator {
  position: absolute;
  top: 0;
  right: 0;
  width: 50px;
  height: 5px;
  z-index: 2;
}

.status-indicator.active {
  background-color: rgb(76, 175, 80);
}

.status-indicator.upcoming {
  background-color: rgb(33, 150, 243);
}

.status-indicator.completed {
  background-color: rgb(158, 158, 158);
}

.text-truncate-3 {  display: -webkit-box;
  -webkit-line-clamp: 3;
  line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

@media (max-width: 600px) {
  .pa-4 {
    padding: 8px !important;
  }
  
  .pa-6 {
    padding: 12px !important;
  }
}
</style>