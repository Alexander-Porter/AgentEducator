<template>
  <v-app-bar app class="header-bar white--text" height="56" density="default">
    <!-- 添加装饰背景 -->
    <div class="header-bg"></div>
    <div class="header-content">
      <v-toolbar-title class="header-title">
        <div class="brand-logo">
          <span class="brand-text">闻道</span>
        </div>
      </v-toolbar-title>
      
      <!-- 课程搜索栏（仅在学生端推荐课程和学习进度页面显示） -->
      <template v-if="showCourseSearchBar">
        <v-menu
          v-model="showCourseSearchResults"
          :close-on-content-click="false"
          location="bottom"
          class="search-results-menu"
          max-width="600"
        >
          <template #activator="{ props }">
            <div class="search-container">
              <v-text-field
                v-model="courseSearchQuery"
                v-bind="props"
                prepend-inner-icon="mdi-magnify"
                label="搜索课程..."
                single-line
                hide-details
                density="compact"
                class="search-field"
                @focus="showCourseSearchResults = true"
                @blur="handleCourseSearchBlur"
                @input="showCourseSearchResults = true"
                autocomplete="off"
                variant="outlined"
              ></v-text-field>
            </div>
          </template>
          <v-card class="search-results-card" elevation="8">
            <v-list v-if="courseSearchResults.length > 0">
              <v-list-item
                v-for="item in courseSearchResults"
                :key="item.id"
                @click="goToCourse(item.id)"
                class="search-result-item"
              >
                <v-list-item-title>{{ item.title }}</v-list-item-title>
                <v-list-item-subtitle>
                  教师：{{ item.teacher }}
                  <span v-if="item.description"> | {{ item.description }}</span>
                </v-list-item-subtitle>
              </v-list-item>
            </v-list>
            <v-card-text v-if="courseStore.loading" class="text-center">
              <v-progress-circular indeterminate color="primary"></v-progress-circular>
              <span class="ms-2">加载课程中...</span>
            </v-card-text>
            <v-card-text v-else-if="courseSearchQuery && courseSearchResults.length === 0 && !courseStore.loading" class="text-center">
              未找到相关课程
            </v-card-text>
          </v-card>
        </v-menu>
      </template>
      
      <v-spacer></v-spacer>
      
      <!-- 用户已登录，显示头像和下拉菜单 -->
      <template v-if="isLoggedIn">
        <div class="user-section">
          <v-menu
            v-model="showDropdown"
            :close-on-content-click="false"
            :close-on-click="true"
            location="bottom end"
            transition="scale-transition"
            offset="10"
            :disabled="!isLoggedIn"
          >
            <template v-slot:activator="{ props }">
              <v-btn 
                icon 
                v-bind="props" 
                class="user-avatar-btn"
                :disabled="!isLoggedIn"
                size="default"
              >
                <v-avatar size="32" class="user-avatar">
                  <img 
                    v-if="userAvatar" 
                    :src="userAvatar" 
                    @error="handleAvatarError" 
                    alt="用户头像"
                    style="width: 100%; height: 100%; object-fit: cover;"
                  />
                  <div v-else class="letter-avatar" :style="letterAvatarStyle">
                    {{ username.charAt(0).toUpperCase() }}
                  </div>
                </v-avatar>
              </v-btn>
            </template>
            
            <v-card class="user-menu-card" elevation="8">
              <v-list>
                <v-list-item to="/profile" @click="showDropdown = false">
                  <template v-slot:prepend>
                    <v-icon>mdi-account</v-icon>
                  </template>
                  <v-list-item-title>个人资料</v-list-item-title>
                </v-list-item>
                <v-list-item to="/settings" @click="showDropdown = false">
                  <template v-slot:prepend>
                    <v-icon>mdi-cog</v-icon>
                  </template>
                  <v-list-item-title>设置</v-list-item-title>
                </v-list-item>
                <v-divider v-if="isTeacher"></v-divider>
                <v-list-item v-if="isTeacher" @click="toggleTeacherView">
                  <template v-slot:prepend>
                    <v-icon>{{ isInTeacherHome ? 'mdi-home' : 'mdi-school' }}</v-icon>
                  </template>
                  <v-list-item-title>{{ isInTeacherHome ? '视频首页' : '教师后台' }}</v-list-item-title>
                </v-list-item>
                <v-divider></v-divider>
                <v-list-item @click="logout" class="logout-item">
                  <template v-slot:prepend>
                    <v-icon>mdi-logout</v-icon>
                  </template>
                  <v-list-item-title>退出登录</v-list-item-title>
                </v-list-item>
              </v-list>
            </v-card>
          </v-menu>
        </div>
      </template>
      
      <!-- 用户未登录，显示登录和注册按钮 -->
      <template v-else>
        <div class="auth-buttons">
          <v-btn to="/login" variant="text" class="auth-btn login-btn">登录</v-btn>
          <v-btn to="/register" variant="outlined" class="auth-btn register-btn">注册</v-btn>
        </div>
      </template>
    </div>
  </v-app-bar>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useUserStore } from '../stores/userStore';
import { useCourseStore } from '../stores/courseStore';
import { API_BASE_URL } from '@/config';
import type { Course } from '../types/course';
import courseService from '../api/courseService'

const router = useRouter();
const route = useRoute();
const userStore = useUserStore();
const courseStore = useCourseStore();
const showDropdown = ref(false);
const avatarLoadError = ref(false);

// 监听登录状态变化，确保登录后菜单不会自动显示
watch(() => userStore.userId, (newId) => {
  if (newId) {
    showDropdown.value = false;
    avatarLoadError.value = false;  // 重置头像加载错误状态
  }
}, { immediate: true });

const username = computed(() => userStore.username || 'User');
const userAvatar = computed(() => {
  if (avatarLoadError.value) return '';  // 如果头像加载失败，返回空字符串以显示首字母头像
  const avatar = userStore.avatar || '';
  if (!avatar) return '';
  // 如果已经是完整URL，直接返回
  if (avatar.startsWith('http')) return avatar;
  // 否则添加baseURL
  return `${API_BASE_URL}${avatar}`;
});
const isLoggedIn = computed(() => !!userStore.userId);
const isTeacher = computed(() => userStore.userRole === 'teacher');

// 计算当前是否在教师后台
const isInTeacherHome = computed(() => {
  return route.meta.layout === 'teacher';
});

// 获取随机颜色
const getRandomColor = (seed: string) => {
  const colors = [
    '#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6',
    '#1abc9c', '#d35400', '#c0392b', '#16a085', '#8e44ad'
  ];
  const index = seed.charCodeAt(0) % colors.length;
  return colors[index];
};

// 首字母头像样式
const letterAvatarStyle = computed(() => {
  const color = getRandomColor(username.value);
  return {
    backgroundColor: color,
    width: '100%',
    height: '100%',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    color: 'white',
    fontWeight: 'bold',
    fontSize: '12px'  // 调整字体大小以适应22px头像
  };
});

// 处理头像加载错误
const handleAvatarError = (e: Event) => {
  console.error('Header img error', e);
  avatarLoadError.value = true;
};

// 监听 store 中的头像变化
watch(() => userStore.avatar, (newAvatar) => {
  console.log('Header: 头像已更新', newAvatar);
  // 确保头像更新时不会触发菜单显示
  showDropdown.value = false;
}, { immediate: true });

// 退出登录
const logout = () => {
  showDropdown.value = false;  // 确保退出时关闭菜单
  userStore.clearUserInfo();
  router.push('/login');
};

// 跳转到教师后台或视频首页
const toggleTeacherView = () => {
  showDropdown.value = false;
  if (isInTeacherHome.value) {
    router.push('/');
  } else {
    router.push('/teacherHome');
  }
};

// 判断当前是否为登录/注册页
const isAuthPage = computed(() => {
  return route.path === '/login' || route.path === '/register';
});

// 只在学生端推荐课程和学习进度页面显示搜索栏
const showCourseSearchBar = computed(() => {
  return route.path === '/' || route.path === '/learning-progress';
});

// 课程搜索相关变量
const courseSearchQuery = ref('');
const showCourseSearchResults = ref(false);

const courseSearchResults = computed(() => {
  if (!courseSearchQuery.value) return [];
  const keyword = courseSearchQuery.value.trim().toLowerCase();
  return courseStore.courses.filter(
    (c: Course) =>
      (c.title && c.title.toLowerCase().includes(keyword)) ||
      (c.teacher && c.teacher.toLowerCase().includes(keyword)) ||
      (c.description && c.description.toLowerCase().includes(keyword))
  );
});

const handleCourseSearchBlur = () => {
  setTimeout(() => {
    showCourseSearchResults.value = false;
  }, 200);
};

const goToCourse = async (courseId: string) => {
  try {
    const response = await courseService.getCourseDetails(courseId);
    if (
      response.status === 200 &&
      response.data.data.videos &&
      response.data.data.videos.length > 0
    ) {
      const firstVideo = response.data.data.videos[0];
      router.push(`/course/${courseId}/video/${firstVideo.id}`);
    } else {
      router.push(`/course/${courseId}`);
    }
  } catch (err) {
    router.push(`/course/${courseId}`);
  }
};

onMounted(() => {
  // 确保组件挂载时菜单是关闭的
  showDropdown.value = false;
});

</script>

<style scoped>
/* 头部栏基础样式 */
.header-bar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #5a67d8 100%) !important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  position: relative;
  overflow: hidden;
}

/* 装饰背景 */
.header-bg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: 
    radial-gradient(circle at 30% 50%, rgba(255, 255, 255, 0.1) 0%, transparent 50%),
    radial-gradient(circle at 70% 50%, rgba(240, 147, 251, 0.1) 0%, transparent 50%);
  pointer-events: none;
  z-index: 1;
}

/* 内容容器 */
.header-content {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  width: 100%;
  height: 100%;
  padding: 0 16px;
}

/* 品牌Logo */
.brand-logo {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  line-height: 1;
}

.brand-text {
  font-size: 18px;
  font-weight: 900;
  letter-spacing: 1px;
  background: linear-gradient(135deg, #fff 0%, rgba(255, 255, 255, 0.9) 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  text-shadow: 0 0 15px rgba(255, 255, 255, 0.3);
}

.brand-subtitle {
  font-size: 9px;
  opacity: 0.8;
  letter-spacing: 0.5px;
  font-weight: 500;
  margin-top: -2px;
}

/* 搜索容器 */
.search-container {
  max-width: 450px;
  min-width: 300px;
  margin: 0 auto;
  flex: 1;
  display: flex;
  justify-content: center;
}

:deep(.search-field) {
  margin: 0 !important;
}

:deep(.search-field .v-field) {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  transition: all 0.3s ease;
}

:deep(.search-field .v-field:hover) {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.3);
}

:deep(.search-field .v-field--focused) {
  background: rgba(255, 255, 255, 0.25);
  border-color: rgba(255, 255, 255, 0.4);
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.1);
}

:deep(.search-field .v-field__input) {
  color: white;
  padding: 0 12px;
}

:deep(.search-field .v-field__prepend-inner .v-icon) {
  color: rgba(255, 255, 255, 0.8);
}

:deep(.search-field .v-label) {
  color: rgba(255, 255, 255, 0.7);
}

/* 搜索结果卡片 */
.search-results-card {
  border-radius: 12px;
  border: 1px solid rgba(0, 0, 0, 0.05);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  margin-top: 8px;
}

.search-result-item {
  transition: background-color 0.2s ease;
}

.search-result-item:hover {
  background-color: rgba(102, 126, 234, 0.1);
}

/* 用户区域 */
.user-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 用户头像按钮 */
.user-avatar-btn {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.15), rgba(255, 255, 255, 0.1));
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

.user-avatar-btn:hover {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.25), rgba(255, 255, 255, 0.15));
  transform: translateY(-1px);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
}

.user-avatar {
  border: 2px solid rgba(255, 255, 255, 0.3);
  transition: all 0.3s ease;
}

.user-avatar-btn:hover .user-avatar {
  border-color: rgba(255, 255, 255, 0.5);
}

/* 用户菜单卡片 */
.user-menu-card {
  border-radius: 12px;
  border: 1px solid rgba(0, 0, 0, 0.05);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  margin-top: 8px;
  min-width: 180px;
}

:deep(.user-menu-card .v-list-item) {
  transition: all 0.2s ease;
  border-radius: 8px;
  margin: 2px 8px;
}

:deep(.user-menu-card .v-list-item:hover) {
  background-color: rgba(102, 126, 234, 0.1);
  transform: translateX(2px);
}

:deep(.user-menu-card .logout-item:hover) {
  background-color: rgba(239, 68, 68, 0.1);
}

/* 认证按钮 */
.auth-buttons {
  display: flex;
  align-items: center;
  gap: 8px;
}

.auth-btn {
  font-weight: 600;
  letter-spacing: 0.5px;
  border-radius: 8px;
  transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  text-transform: none;
}

.login-btn {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.15), rgba(255, 255, 255, 0.1));
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.login-btn:hover {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.25), rgba(255, 255, 255, 0.15));
  transform: translateY(-1px);
}

.register-btn {
  background: rgba(255, 255, 255, 0.9);
  color: #667eea !important;
  border: 1px solid rgba(255, 255, 255, 0.5);
  font-weight: 700;
}

.register-btn:hover {
  background: white;
  transform: translateY(-1px);
  box-shadow: 0 4px 15px rgba(255, 255, 255, 0.3);
}

/* 兼容性样式 */
:deep(.v-toolbar__content) {
  padding: 0 !important;
}

:deep(.v-app-bar__content) {
  padding: 0 !important;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .search-container {
    max-width: 250px;
    min-width: 200px;
    margin: 0 10px;
  }
  
  .brand-subtitle {
    display: none;
  }
  
  .brand-text {
    font-size: 16px;
  }
}

@media (max-width: 600px) {
  .search-container {
    max-width: 180px;
    min-width: 150px;
    margin: 0 8px;
  }
  
  .header-content {
    padding: 0 12px;
  }
}
</style>
