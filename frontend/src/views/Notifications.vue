<template>
  <div class="notifications-container">
    <v-container fluid>
      <v-card class="content-card">
        <v-card-title class="d-flex align-center py-4 px-6">
          通知管理
          <v-spacer></v-spacer>
          <v-btn color="primary" prepend-icon="mdi-plus">
            发送新通知
          </v-btn>
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text class="pa-6">
          <div class="notification-list">
            <v-list lines="two">
              <v-list-item
                v-for="notification in notifications"
                :key="notification.id"
                :value="notification"
                rounded="lg"
                class="mb-3"
              >
                <template v-slot:prepend>
                  <v-avatar :color="getNotificationColor(notification.type)" class="mr-3">
                    <v-icon :icon="getNotificationIcon(notification.type)" color="white"></v-icon>
                  </v-avatar>
                </template>
                
                <v-list-item-title class="font-weight-bold mb-1">
                  {{ notification.title }}
                </v-list-item-title>
                
                <v-list-item-subtitle>
                  {{ notification.message }}
                </v-list-item-subtitle>
                
                <template v-slot:append>
                  <div class="d-flex flex-column align-end">
                    <div class="text-caption text-grey">
                      {{ notification.date }}
                    </div>
                    <div class="mt-2">
                      <v-chip
                        :color="notification.sent ? 'success' : 'warning'"
                        size="small"
                        variant="outlined"
                      >
                        {{ notification.sent ? '已发送' : '草稿' }}
                      </v-chip>
                    </div>
                  </div>
                </template>
              </v-list-item>
            </v-list>
          </div>
        </v-card-text>
      </v-card>
    </v-container>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';

const notifications = ref([
  {
    id: 1,
    title: '课程作业发布通知',
    message: '《Vue.js基础入门》第一章习题已发布，请按时完成。',
    date: '2025-05-05',
    type: 'assignment',
    sent: true
  },
  {
    id: 2,
    title: '课程延期通知',
    message: '由于教师工作安排，本周五的《JavaScript高级编程》课程将延期至下周一。',
    date: '2025-05-04',
    type: 'calendar',
    sent: true
  },
  {
    id: 3,
    title: '系统维护通知',
    message: '系统将于本周六凌晨2点至4点进行维护，届时系统将不可用。',
    date: '2025-05-03',
    type: 'system',
    sent: true
  },
  {
    id: 4,
    title: '期中考试安排',
    message: '本学期期中考试将于5月20日至5月25日进行，请各位同学提前准备。',
    date: '2025-05-02',
    type: 'exam',
    sent: false
  }
]);

const getNotificationColor = (type: string) => {
  switch (type) {
    case 'assignment': return 'primary';
    case 'calendar': return 'info';
    case 'system': return 'warning';
    case 'exam': return 'error';
    default: return 'grey';
  }
};

const getNotificationIcon = (type: string) => {
  switch (type) {
    case 'assignment': return 'mdi-book-open-variant';
    case 'calendar': return 'mdi-calendar-alert';
    case 'system': return 'mdi-cog';
    case 'exam': return 'mdi-clipboard-text';
    default: return 'mdi-bell';
  }
};

onMounted(() => {
  // 这里可以加载通知数据
});
</script>

<style scoped>
.notifications-container {
  width: 100%;
  height: 100%;
}

.content-card {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  height: 100%;
}

.notification-list {
  max-height: calc(100vh - 200px);
  overflow-y: auto;
}
</style>