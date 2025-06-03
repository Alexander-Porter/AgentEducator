<template>
  <div class="task-monitor">
    <v-container fluid class="pa-4">
      <v-card class="content-card">
        <v-card-title class="d-flex align-center py-4 px-6">
          视频处理任务监控
          <v-spacer></v-spacer>
          <div class="refresh-control">
            <label>
              <input type="checkbox" v-model="autoRefresh"> 自动刷新
            </label>
            <select v-model="refreshInterval" @change="handleRefreshIntervalChange">
              <option :value="5000">5秒</option>
              <option :value="10000">10秒</option>
              <option :value="30000">30秒</option>
              <option :value="60000">1分钟</option>
            </select>
            <button class="refresh-btn" @click="refreshData">
              <i class="fas fa-sync-alt" :class="{ 'fa-spin': isRefreshing }"></i> 刷新
            </button>
          </div>
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text class="pa-4">
          <div class="tasks-container">
            <div class="tasks-list">
              <div class="section-header">
                <h2>处理任务列表</h2>
                <div class="filter-group">
                  <select v-model="statusFilter" @change="fetchTasks">
                    <option value="">所有状态</option>
                    <option value="pending">等待处理</option>
                    <option value="processing">处理中</option>
                    <option value="completed">已完成</option>
                    <option value="failed">失败</option>
                    <option value="cancelled">已取消</option>
                  </select>
                </div>
              </div>
              
              <div class="tasks-grid">
                <div 
                  v-for="task in tasks" 
                  :key="task.task_id" 
                  :class="['task-card', { active: selectedTaskId === task.task_id }]"
                  @click="selectTask(task.task_id)"
                >
                  <div class="task-thumbnail">
                    <img :src="task.video_cover || '/temp_img/default_video_thumbnail.jpg'" :alt="task.video_title">
                    <div 
                      class="status-badge" 
                      :class="{
                        'pending': task.status === 'pending',
                        'processing': task.status === 'processing',
                        'completed': task.status === 'completed',
                        'failed': task.status === 'failed',
                        'cancelled': task.status === 'cancelled'
                      }"
                    >
                      {{ getStatusText(task.status) }}
                    </div>
                  </div>
                  <div class="task-info">
                    <div class="task-title">{{ task.video_title }}</div>
                    <div class="task-progress">
                      <div class="progress-bar">
                        <div class="progress-fill" :style="{ width: Math.round(task.progress * 100) + '%' }"></div>
                      </div>
                      <div class="progress-text">{{ Math.round(task.progress * 100) }}%</div>
                    </div>
                    <div class="task-time">
                      <span>创建于: {{ formatDate(task.start_time) }}</span>
                    </div>
                  </div>
                </div>
              </div>
              
              <div v-if="loading" class="loading-section">
                <div class="spinner"></div>
                <p>加载中...</p>
              </div>
              
              <div v-if="!loading && tasks.length === 0" class="empty-section">
                <i class="fas fa-tasks"></i>
                <p>没有找到视频处理任务</p>
              </div>
              
              <div v-if="totalPages > 1" class="pagination">
                <button 
                  class="page-btn" 
                  :disabled="currentPage === 1"
                  @click="changePage(currentPage - 1)"
                >
                  上一页
                </button>
                <div class="page-info">{{ currentPage }} / {{ totalPages }}</div>
                <button 
                  class="page-btn" 
                  :disabled="currentPage === totalPages"
                  @click="changePage(currentPage + 1)"
                >
                  下一页
                </button>
              </div>
            </div>
            
            <div class="task-logs">
              <div class="section-header">
                <h2>处理日志</h2>
                <div v-if="selectedTask" class="task-actions">
                  <div class="task-status-info">
                    状态: <span :class="'status-' + selectedTask.status">{{ getStatusText(selectedTask.status) }}</span>
                  </div>
                  <v-btn
                    color="error"
                    variant="outlined"
                    size="small"
                    :loading="isDeleting"
                    :disabled="isDeleting"
                    prepend-icon="mdi-delete"
                    @click="confirmDeleteTask"
                  >
                    删除任务
                  </v-btn>
                </div>
              </div>
              
              <div v-if="!selectedTaskId" class="no-task-selected">
                <i class="fas fa-clipboard-list"></i>
                <p>选择左侧任务查看详细日志</p>
              </div>
              
              <div v-else-if="logsLoading" class="logs-loading">
                <div class="spinner"></div>
                <p>加载日志中...</p>
              </div>
              
              <div v-else class="logs-content">
                <div class="task-progress-detail">
                  <div class="progress-header">
                    <h3>处理进度</h3>
                    <div class="progress-percentage">{{ Math.round((selectedTask?.progress || 0) * 100) }}%</div>
                  </div>
                  <div class="progress-bar">
                    <div class="progress-fill" :style="{ width: Math.round((selectedTask?.progress || 0) * 100) + '%' }"></div>
                  </div>
                  <div class="task-time-info">
                    <div>开始时间: {{ formatTime(selectedTask?.start_time) }}</div>
                    <div>{{ selectedTask?.end_time ? '结束时间: ' + formatTime(selectedTask.end_time) : '处理中...' }}</div>
                    <div v-if="selectedTask?.start_time && selectedTask?.end_time">
                      耗时: {{ calculateDuration(selectedTask.start_time, selectedTask.end_time) }}
                    </div>
                  </div>
                </div>
                
                <div class="logs-list">
                  <div 
                    v-for="log in logs" 
                    :key="log.id" 
                    :class="['log-item', 'log-' + log.log_level]"
                  >
                    <div class="log-timestamp">{{ formatTime(log.timestamp) }}</div>
                    <div class="log-content">{{ log.message }}</div>
                  </div>
                </div>
                
                <div v-if="logs.length === 0" class="no-logs">
                  <p>该任务暂无处理日志</p>
                </div>
                
                <div v-if="selectedTask && (selectedTask.status === 'failed' || selectedTask.status === 'cancelled') && selectedTask.error_message" class="error-message">
                  <h3>错误信息</h3>
                  <div class="error-content">{{ selectedTask.error_message }}</div>
                </div>
              </div>
            </div>
          </div>
        </v-card-text>
      </v-card>
    </v-container>
    
    <!-- 删除确认对话框 -->
    <v-dialog v-model="showDeleteConfirm" max-width="500">
      <v-card>
        <v-card-title class="text-error">
          <v-icon start icon="mdi-alert" color="error" class="mr-2"></v-icon>
          确认删除任务
        </v-card-title>
        
        <v-card-text>
          <p>您确定要删除此任务及其所有日志吗？</p>
          <v-alert
            v-if="selectedTask && selectedTask.status === 'processing'"
            type="warning"
            variant="tonal"
            class="mt-3"
          >
            <strong>警告</strong>: 该任务正在处理中，删除将会<strong>终止处理进程</strong>！
          </v-alert>
        </v-card-text>
        
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn
            color="default"
            variant="text"
            @click="showDeleteConfirm = false"
          >
            取消
          </v-btn>
          <v-btn
            color="error"
            variant="flat"
            :loading="isDeleting"
            :disabled="isDeleting"
            @click="deleteTask"
          >
            {{ isDeleting ? '删除中...' : '确认删除' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useUserStore } from '../../stores/userStore';
import taskService from '../../api/taskService';
import { teacherNavItems } from '../../config/navigation'; 

export default {
  name: 'TaskMonitor',
  setup() {
    // 状态变量
    const userStore = useUserStore();
    const router = useRouter();
    const tasks = ref([]);
    const loading = ref(false);
    const currentPage = ref(1);
    const totalPages = ref(1);
    const pageSize = ref(12);
    const statusFilter = ref('');
    const selectedTaskId = ref(null);
    const selectedTask = ref(null);
    const logs = ref([]);
    const logsLoading = ref(false);
    const autoRefresh = ref(true);
    const refreshInterval = ref(10000);
    const refreshTimer = ref(null);
    const isRefreshing = ref(false);
    const showDeleteConfirm = ref(false);
    const isDeleting = ref(false);
    
    // 获取任务列表
    const fetchTasks = async () => {
      loading.value = true;
      try {
        const response = await taskService.getTasksList({
          page: currentPage.value,
          size: pageSize.value,
          status: statusFilter.value || undefined
        });
        
        if (response.data.code === 200) {
          tasks.value = response.data.data.list;
          totalPages.value = Math.ceil(response.data.data.total / pageSize.value);
          
          // 如果当前选中的任务在列表中，更新其信息
          if (selectedTaskId.value) {
            const updatedTask = tasks.value.find(task => task.task_id === selectedTaskId.value);
            if (updatedTask) {
              selectedTask.value = updatedTask;
            }
          }
        } else {
          console.error('获取任务列表失败:', response.msg);
        }
      } catch (error) {
        console.error('获取任务列表出错:', error);
      } finally {
        loading.value = false;
        isRefreshing.value = false;
      }
    };
    
    // 获取任务日志
    const fetchTaskLogs = async (taskId) => {
      if (!taskId) return;
      
      logsLoading.value = true;
      try {
        const response = await taskService.getTaskLogs(taskId);
        
        if (response.data.code === 200) {
          logs.value = response.data.data.logs;
          selectedTask.value = response.data.data.task;
        } else {
          console.error('获取任务日志失败:', response.msg);
        }
      } catch (error) {
        console.error('获取任务日志出错:', error);
      } finally {
        logsLoading.value = false;
      }
    };
    
    // 选择任务
    const selectTask = (taskId) => {
      selectedTaskId.value = taskId;
      fetchTaskLogs(taskId);
    };
    
    // 切换页面
    const changePage = (page) => {
      currentPage.value = page;
      fetchTasks();
    };
    
    // 刷新数据
    const refreshData = () => {
      isRefreshing.value = true;
      fetchTasks();
      
      if (selectedTaskId.value) {
        fetchTaskLogs(selectedTaskId.value);
      }
    };
    
    // 设置自动刷新
    const setupAutoRefresh = () => {
      clearAutoRefresh();
      
      if (autoRefresh.value) {
        refreshTimer.value = setInterval(refreshData, refreshInterval.value);
      }
    };
    
    // 清除自动刷新
    const clearAutoRefresh = () => {
      if (refreshTimer.value) {
        clearInterval(refreshTimer.value);
        refreshTimer.value = null;
      }
    };
    
    // 当刷新间隔改变时
    const handleRefreshIntervalChange = () => {
      setupAutoRefresh();
    };
    
    // 确认删除任务
    const confirmDeleteTask = () => {
      if (!selectedTaskId.value) return;
      showDeleteConfirm.value = true;
    };
    
    // 删除任务
    const deleteTask = async () => {
      if (!selectedTaskId.value) return;
      
      isDeleting.value = true;
      try {
        const response = await taskService.deleteTask(selectedTaskId.value);
        
        if (response.data.code === 200) {
          // 隐藏确认对话框
          showDeleteConfirm.value = false;
          
          // 重新加载任务列表
          fetchTasks();
          
          // 清空当前选择
          selectedTaskId.value = null;
          selectedTask.value = null;
          logs.value = [];
          
          // 显示成功消息
          alert('任务已成功删除');
        } else {
          console.error('删除任务失败:', response.data.msg);
          alert('删除任务失败: ' + response.data.msg);
        }
      } catch (error) {
        console.error('删除任务出错:', error);
        alert('删除任务出错: ' + (error.message || '未知错误'));
      } finally {
        isDeleting.value = false;
      }
    };
    
    // 获取状态文本
    const getStatusText = (status) => {
      const statusMap = {
        'pending': '等待处理',
        'processing': '处理中',
        'completed': '已完成',
        'failed': '失败',
        'cancelled': '已取消'
      };
      return statusMap[status] || status;
    };
    
    // 格式化日期
    const formatDate = (dateString) => {
      if (!dateString) return '';
      const date = new Date(dateString);
      return date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
    };
    
    // 格式化时间
    const formatTime = (dateString) => {
      if (!dateString) return '';
      const date = new Date(dateString);
      return date.toLocaleString('zh-CN', { 
        year: 'numeric', 
        month: '2-digit', 
        day: '2-digit', 
        hour: '2-digit', 
        minute: '2-digit', 
        second: '2-digit' 
      });
    };
    
    // 计算任务持续时间
    const calculateDuration = (startTime, endTime) => {
      if (!startTime || !endTime) return '';
      
      const start = new Date(startTime);
      const end = new Date(endTime);
      const diffMs = end - start;
      
      const diffSec = Math.floor(diffMs / 1000);
      const minutes = Math.floor(diffSec / 60);
      const seconds = diffSec % 60;
      
      if (minutes > 0) {
        return `${minutes}分${seconds}秒`;
      } else {
        return `${seconds}秒`;
      }
    };
    
    // 登出
    const logout = () => {
      userStore.clearUserInfo();
      router.push('/login');
    };
    
    // 监听自动刷新的改变
    watch(autoRefresh, (newValue) => {
      if (newValue) {
        setupAutoRefresh();
      } else {
        clearAutoRefresh();
      }
    });
    
    // 组件挂载时
    onMounted(() => {
      fetchTasks();
      setupAutoRefresh();
    });
    
    // 组件卸载前
    onBeforeUnmount(() => {
      clearAutoRefresh();
    });
    
    return {
      userStore,
      tasks,
      loading,
      currentPage,
      totalPages,
      statusFilter,
      selectedTaskId,
      selectedTask,
      logs,
      logsLoading,
      autoRefresh,
      refreshInterval,
      isRefreshing,
      showDeleteConfirm,
      isDeleting,
      fetchTasks,
      selectTask,
      changePage,
      refreshData,
      handleRefreshIntervalChange,
      confirmDeleteTask,
      deleteTask,
      getStatusText,
      formatDate,
      formatTime,
      calculateDuration,
      logout
    };
  }
};
</script>

<style scoped>
.task-monitor {
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

/* 刷新控制 */
.refresh-control {
  display: flex;
  align-items: center;
  gap: 10px;
}

.refresh-control label {
  display: flex;
  align-items: center;
  gap: 5px;
}

.refresh-control select {
  padding: 5px;
  border-radius: 4px;
  border: 1px solid #ddd;
}

.refresh-btn {
  padding: 5px 10px;
  background-color: #f5f5f5;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
}

.fa-spin {
  animation: fa-spin 2s infinite linear;
}

@keyframes fa-spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 内容区域 */
.tasks-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  height: calc(100vh - 180px);
}

.tasks-list, .task-logs {
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  padding: 20px;
  display: flex;
  flex-direction: column;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-header h2 {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
}

.filter-group select {
  padding: 8px;
  border-radius: 4px;
  border: 1px solid #ddd;
}

/* 任务卡片 */
.tasks-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 15px;
  overflow-y: auto;
  max-height: calc(100% - 90px);
}

.task-card {
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  transition: all 0.3s ease;
  cursor: pointer;
  border: 2px solid transparent;
}

.task-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.task-card.active {
  border-color: #6f23d1;
}

.task-thumbnail {
  height: 120px;
  overflow: hidden;
  position: relative;
}

.task-thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.status-badge {
  position: absolute;
  top: 10px;
  right: 10px;
  padding: 3px 8px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
  color: white;
}

.status-badge.pending {
  background-color: #f39c12;
}

.status-badge.processing {
  background-color: #3498db;
}

.status-badge.completed {
  background-color: #2ecc71;
}

.status-badge.failed {
  background-color: #e74c3c;
}

.status-badge.cancelled {
  background-color: #7f8c8d;
}

.task-info {
  padding: 12px;
}

.task-title {
  font-weight: 500;
  margin-bottom: 8px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.task-progress {
  margin-bottom: 8px;
}

.progress-bar {
  height: 6px;
  background-color: #ecf0f1;
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 5px;
}

.progress-fill {
  height: 100%;
  background-color: #6f23d1;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 12px;
  text-align: right;
}

.task-time {
  font-size: 12px;
  color: #7f8c8d;
}

/* 日志区域 */
.task-logs {
  overflow: hidden;
}

.task-actions {
  display: flex;
  align-items: center;
  gap: 15px;
}

.task-status-info {
  display: flex;
  align-items: center;
  font-weight: 500;
}

.task-status-info .status-pending {
  color: #f39c12;
}

.task-status-info .status-processing {
  color: #3498db;
}

.task-status-info .status-completed {
  color: #2ecc71;
}

.task-status-info .status-failed {
  color: #e74c3c;
}

.task-status-info .status-cancelled {
  color: #7f8c8d;
}

.delete-btn {
  padding: 5px 10px;
  background-color: #ffe6e6;
  color: #e74c3c;
  border: 1px solid #e74c3c;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s ease;
}

.delete-btn:hover {
  background-color: #e74c3c;
  color: white;
}

.delete-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.logs-content {
  display: flex;
  flex-direction: column;
  height: calc(100% - 40px);
}

.task-progress-detail {
  margin-bottom: 15px;
  padding: 15px;
  background-color: #f8f9fa;
  border-radius: 5px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.progress-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.task-time-info {
  display: flex;
  justify-content: space-between;
  margin-top: 10px;
  font-size: 13px;
  color: #7f8c8d;
}

.logs-list {
  flex: 1;
  overflow-y: auto;
  border: 1px solid #eee;
  border-radius: 5px;
  padding: 10px;
}

.log-item {
  padding: 8px;
  margin-bottom: 5px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 13px;
  display: flex;
  border-left: 4px solid transparent;
}

.log-item:last-child {
  margin-bottom: 0;
}

.log-info {
  background-color: #f8f9fa;
  border-left-color: #3498db;
}

.log-warning {
  background-color: #fff8e1;
  border-left-color: #f39c12;
}

.log-error {
  background-color: #fdecea;
  border-left-color: #e74c3c;
}

.log-timestamp {
  width: 160px;
  flex-shrink: 0;
  color: #7f8c8d;
}

.log-content {
  flex: 1;
}

.error-message {
  margin-top: 15px;
  padding: 15px;
  background-color: #fdecea;
  border-radius: 5px;
  border-left: 4px solid #e74c3c;
}

.error-message h3 {
  margin: 0 0 10px 0;
  font-size: 16px;
  color: #c0392b;
}

.error-content {
  font-family: monospace;
  white-space: pre-wrap;
  word-break: break-word;
}

/* 加载和空状态 */
.loading-section, .empty-section, .no-task-selected, .logs-loading, .no-logs {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 40px;
  color: #95a5a6;
}

.spinner {
  border: 4px solid rgba(0, 0, 0, 0.1);
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border-left-color: #6f23d1;
  animation: spin 1s linear infinite;
  margin-bottom: 15px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.empty-section i, .no-task-selected i {
  font-size: 40px;
  margin-bottom: 15px;
}

/* 分页控制 */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: 20px;
}

.page-btn {
  padding: 8px 12px;
  background-color: #f5f5f5;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  margin: 0 15px;
}

/* 删除确认对话框 */
.delete-confirm-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.delete-confirm-content {
  background-color: white;
  border-radius: 8px;
  padding: 20px;
  width: 90%;
  max-width: 450px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.delete-confirm-content h3 {
  margin-top: 0;
  color: #e74c3c;
}

.warning-text {
  color: #e74c3c;
}

.delete-confirm-buttons {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
  gap: 10px;
}

.cancel-btn {
  padding: 8px 16px;
  background-color: #f5f5f5;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
}

.confirm-btn {
  padding: 8px 16px;
  background-color: #e74c3c;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.confirm-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
