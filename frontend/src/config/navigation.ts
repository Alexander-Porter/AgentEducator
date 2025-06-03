/**
 * 系统导航配置
 * 集中管理所有导航项，便于统一维护
 */

// 教师端导航配置
export const teacherNavItems = [
  { id: 1, title: '首页', path: '/teacherHome', icon: 'fas fa-home' },
  { id: 2, title: '课程管理', path: '/courses', icon: 'fas fa-book' },
  { id: 3, title: '视频上传', path: '/videos', icon: 'fas fa-video' },
  { id: 4, title: '学生管理', path: '/students', icon: 'fas fa-user-graduate' },
  { id: 5, title: '作业批改', path: '/assignments', icon: 'fas fa-tasks' },
  { id: 6, title: '数据统计', path: '/statistics', icon: 'fas fa-chart-line' },
  { id: 7, title: '任务日志', path: '/task-monitor', icon: 'fas fa-clipboard-list' },
  { id: 8, title: '系统设置', path: '/settings', icon: 'fas fa-cog' }
];


// 默认导出所有导航配置
export default {
  teacher: teacherNavItems
};
