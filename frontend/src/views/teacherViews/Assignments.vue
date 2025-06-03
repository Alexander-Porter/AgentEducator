<template>
  <div class="assignments-container">
    <v-container fluid>
      <v-card class="content-card">
        <v-card-title class="d-flex align-center py-4 px-6">
          作业管理
          <v-spacer></v-spacer>
          <v-btn color="primary" prepend-icon="mdi-plus">
            新建作业
          </v-btn>
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text class="pa-6">
          <v-data-table
            :headers="headers"
            :items="assignments"
            :loading="loading"
            class="elevation-1"
          >
            <template v-slot:item.status="{ item }">
              <v-chip
                :color="getStatusColor(item.status)"
                :text-color="getStatusTextColor(item.status)"
                size="small"
              >
                {{ item.status }}
              </v-chip>
            </template>
            <template v-slot:item.actions="{ item }">
              <v-btn icon variant="text" size="small" color="primary">
                <v-icon>mdi-pencil</v-icon>
              </v-btn>
              <v-btn icon variant="text" size="small" color="primary">
                <v-icon>mdi-eye</v-icon>
              </v-btn>
              <v-btn icon variant="text" size="small" color="error">
                <v-icon>mdi-delete</v-icon>
              </v-btn>
            </template>
          </v-data-table>
        </v-card-text>
      </v-card>
    </v-container>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useUserStore } from '../../stores/userStore';
//import assignmentService from '../../api/assignmentService';

const loading = ref(true);
const assignments = ref([
  {
    id: 1,
    title: '第一章习题',
    course: 'Vue.js基础入门',
    dueDate: '2025-05-15',
    status: '进行中',
    submissions: 24
  },
  {
    id: 2,
    title: '第二章课后作业',
    course: 'Vue.js基础入门',
    dueDate: '2025-05-20',
    status: '未开始',
    submissions: 0
  },
  {
    id: 3,
    title: '期中项目作业',
    course: 'JavaScript高级编程',
    dueDate: '2025-06-10',
    status: '已结束',
    submissions: 35
  }
]);

const headers = [
  { title: 'ID', align: 'start', key: 'id' },
  { title: '作业标题', align: 'start', key: 'title' },
  { title: '课程', align: 'start', key: 'course' },
  { title: '截止日期', align: 'start', key: 'dueDate' },
  { title: '状态', align: 'start', key: 'status' },
  { title: '提交数', align: 'start', key: 'submissions' },
  { title: '操作', align: 'center', key: 'actions', sortable: false }
];

const getStatusColor = (status: string) => {
  switch (status) {
    case '进行中': return 'success';
    case '未开始': return 'info';
    case '已结束': return 'grey';
    default: return 'grey';
  }
};

const getStatusTextColor = (status: string) => {
  return 'white';
};

onMounted(() => {
  // 模拟API请求延迟
  setTimeout(() => {
    loading.value = false;
  }, 1000);
});
</script>

<style scoped>
.assignments-container {
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
</style>