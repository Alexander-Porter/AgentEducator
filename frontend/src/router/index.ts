import { createRouter, createWebHistory } from 'vue-router'
import type { RouteLocationNormalized, NavigationGuardNext } from 'vue-router'
import Home from '../views/Home.vue'
import VideoPlayer from '../views/VideoPlayer.vue'
import CourseView from '../views/CourseView.vue'
import Login from "../views/Login.vue";
import Register from "../views/Register.vue";
import TeacherHome from "../views/teacherViews/TeacherHome.vue";
import Videos from "../views/teacherViews/VideosUpload.vue";
import CourseManagement from "../views/teacherViews/CourseAdmin.vue";
import UserProfile from "../views/UserProfile.vue";
import LearningProgress from "../views/LearningProgress.vue"
import Notebook from "../views/Notebook.vue"
import AIAssistant from "../views/AIAssistant.vue"
import StudentManagement from '../views/teacherViews/StudentManagement.vue';
import TaskMonitor from '../views/teacherViews/TaskMonitor.vue';
import PersonalizedRecommend from '../views/PersonalizedRecommend.vue'
import Statistics from '../views/teacherViews/Statistics.vue';
import AllCourses from '../views/AllCourses.vue';
// 导入课程视频管理组件
import CourseVideosManage from '../views/teacherViews/components/CourseVideosManage.vue';
// 导入缺少的组件或使用动态导入
const Assignments = () => import('../views/teacherViews/Assignments.vue')
const Notifications = () => import('../views/Notifications.vue')


const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: Home,
      meta: { layout: 'default' }
    },    {
      path: '/course/:courseId/video/:videoId',
      name: 'videoPlayer',
      component: VideoPlayer,
      meta: { layout: 'blank' }  // 修改为blank布局，没有侧边栏
    },
    {
      path: '/course/:courseId',
      name: 'courseView',
      component: () => import('../views/CourseView.vue'),
      meta: { layout: 'blank' }  // 使用blank布局，因为这是一个重定向页面
    },
    { 
      path: '/login', 
      component: Login,
      meta: { layout: 'blank' } 
    },
    { 
      path: '/register',
      component: Register,
      meta: { layout: 'blank' } 
    },
    { 
      path: '/teacherHome',
      component: TeacherHome,
      meta: { layout: 'teacher' }
    },
    { 
      path: '/videos', 
      name: 'VideosUpload',
      component: Videos,
      meta: { layout: 'teacher' }
    },
    { 
      path: '/courses', 
      component: CourseManagement,
      meta: { layout: 'teacher' }
    },
    { 
      path: '/profile', 
      component: UserProfile,
      meta: { layout: 'default' }
    },
    {
      path: '/task-monitor',
      name: 'TaskMonitor',
      component: TaskMonitor,
      meta: { 
        requiresAuth: true,
        roles: ['teacher', 'admin'],
        layout: 'teacher'
      }
    },
    // 添加数据统计路由
    {
      path: '/statistics',
      name: 'Statistics',
      component: Statistics,
      meta: { 
        requiresAuth: true,
        roles: ['teacher', 'admin'],
        layout: 'teacher'
      }
    },
    // 添加缺少的路由
    {
      path: '/assignments',
      name: 'assignments',
      component: Assignments,
      meta: { 
        requiresAuth: true, 
        roles: ['teacher'], 
        layout: 'teacher' 
      }
    },
    {
      path: '/notifications',
      name: 'notifications',
      component: Notifications,
      meta: { 
        requiresAuth: true, 
        roles: ['teacher'], 
        layout: 'teacher' 
      }
    },
    
    // 学生相关路由
    { 
      path: '/learning-progress', 
      name: 'learningProgress', 
      component: LearningProgress,
      meta: { layout: 'default' }
    },
    { 
      path: '/notebook', 
      name: 'notebook', 
      component: Notebook,
      meta: { layout: 'default' }
    },
    { 
      path: '/ai-assistant', 
      name: 'aiAssistant', 
      component: AIAssistant,
      meta: { layout: 'default' }
    },
    { 
      path: '/students',
      name: 'studentManagement',
      component: StudentManagement,
      meta: { layout: 'teacher' }
    },
    {
      path: '/CourseVideoManage/:id',
      name: 'courseVideosManage',
      component: CourseVideosManage,
      meta: { 
        requiresAuth: true, 
        roles: ['teacher'], 
        layout: 'teacher' 
      }
    },    {
      path: '/all-courses',
      name: 'allCourses',
      component: AllCourses,
      meta: { layout: 'default' }
    },
    {

      path: '/personalized',
      name: 'personalized',
      component: PersonalizedRecommend,
      meta: { layout: 'default' }
    },
    {

      path: '/knowledge-map',
      name: 'KnowledgeMap',
      component: () => import('../views/KnowledgeMap.vue'),
      meta: {
        requiresAuth: true,
        title: '知识图谱'
      }
    },
    // 移动端视频播放器路由
    {
      path: '/mobile/course/:courseId/video/:videoId',
      name: 'MobileVideoPlayer',
      component: () => import('../views/MobileVideoPlayer.vue'),
      meta: { 
        requiresAuth: true,
        layout: 'blank'
      }
    },
    { path: '/:pathMatch(.*)*', redirect: '/' }
  ]
})

// 全局导航守卫，验证用户是否登录
router.beforeEach((to: RouteLocationNormalized, from: RouteLocationNormalized, next: NavigationGuardNext) => {
  const publicPages = ['/', '/login', '/register', '/learning-progress', '/notebook', '/ai-assistant'];
  const token = localStorage.getItem('wendao_token');

  const authRequired = !publicPages.includes(to.path);

  if (authRequired && !token) {
    return next('/login');
  }

  if ((to.path === '/login' || to.path === '/register') && token) {
    return next('/');
  }

  next();
});


export default router