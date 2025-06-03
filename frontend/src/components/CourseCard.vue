<template>
  <v-card class="course-card" @click="navigateToVideo">
    <v-img
      :src="thumbnail"
      :alt="title"
      height="200"
      cover
    >
      <template v-slot:placeholder>
        <v-row
          class="fill-height ma-0"
          align="center"
          justify="center"
        >
          <v-progress-circular
            indeterminate
            color="primary"
          ></v-progress-circular>
        </v-row>
      </template>
    </v-img>

    <v-card-text>
      <div class="d-flex justify-space-between align-center mb-2">
        <v-chip
          size="small"
          color="primary"
          variant="tonal"
        >
          {{ duration }}
        </v-chip>        <div class="d-flex align-center" v-if="rating">
          <v-icon size="small" color="warning" class="mr-1">mdi-star</v-icon>
          <span class="text-caption">{{ rating }}</span>
        </div>
      </div>

      <v-card-title class="text-subtitle-1 pa-0">{{ title }}</v-card-title>
      
      <div class="d-flex align-center mt-2">
        <v-avatar size="24" class="mr-2">
          <v-img src="https://picsum.photos/24/24"></v-img>
        </v-avatar>
        <span class="text-caption">{{ teacher }}</span>
        <v-divider vertical class="mx-2"></v-divider>
        <span class="text-caption">{{ category }}</span>
      </div>

      <div class="d-flex align-center mt-2">
        <v-icon size="small" color="grey" class="mr-1">mdi-account-group</v-icon>
        <span class="text-caption">{{ students }}人在学</span>
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import courseService from '../api/courseService'

const router = useRouter()

const props = defineProps<{
  id: string
  thumbnail: string
  title: string
  duration: string
  students: number
  rating?: number // 使评分可选
  teacher: string
  category: string
}>()

// 点击课程卡片导航到视频播放页面
const navigateToVideo = async () => {
  try {
    console.log('获取课程详情, 课程ID:', props.id)
    // 获取课程详情，包括视频列表
    const response = await courseService.getCourseDetails(props.id)
    console.log('课程详情响应:', response)
    
    if (response.status === 200 && response.data.data.videos && response.data.data.videos.length > 0) {
      // 有视频，导航到第一个视频
      const firstVideo = response.data.data.videos[0]
      console.log('正在导航到视频:', firstVideo.id)
      router.push(`/course/${props.id}/video/${firstVideo.id}`)
    } else {
      // 无视频，导航到课程详情页
      console.warn('此课程暂无视频或返回数据异常:', response)
      router.push(`/course/${props.id}`)
      console.log('此课程暂无视频')
    }
  } catch (err) {
    console.error('获取课程视频失败:', err)
    // 出错时导航到课程详情页
    router.push(`/course/${props.id}`)
  }
}
</script>

<style scoped>
.course-card {
  cursor: pointer;
  transition: all 0.3s ease;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.course-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 25px 0 rgba(0, 0, 0, 0.1);
}
</style>