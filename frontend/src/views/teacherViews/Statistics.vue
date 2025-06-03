<template>
  <div class="statistics-view">
    <v-container fluid class="pa-4 teacher-container">
      <v-card class="content-card mb-4">
        <v-card-title class="d-flex align-center py-4 px-6">
          <div class="d-flex align-center">
            <v-icon color="primary" class="mr-2">mdi-chart-areaspline</v-icon>
            <span class="text-h5">教学数据统计</span>
          </div>
          <v-spacer></v-spacer>
          
          <!-- 顶部筛选器 -->
          <div class="d-flex align-center">
            <v-select
              v-model="selectedCourse"
              :items="courses"
              item-title="name"
              item-value="id"
              label="选择课程"
              hide-details
              variant="outlined"
              density="compact"
              class="mr-2"
              style="min-width: 200px;"
              prepend-inner-icon="mdi-book-open-variant"
              @update:modelValue="loadStatistics"
            ></v-select>
            
            <v-select
              v-model="timePeriod"
              :items="timePeriods"
              label="时间周期"
              hide-details
              variant="outlined"
              density="compact"
              class="mr-2"
              style="width: 150px;"
              prepend-inner-icon="mdi-calendar-range"
              @update:modelValue="loadStatistics"
            ></v-select>
            
            <v-btn color="primary" @click="refreshData" class="ml-2">
              <v-icon start>mdi-refresh</v-icon>
              刷新
            </v-btn>
          </div>
        </v-card-title>
        
        <v-divider></v-divider>        <v-card-text class="pa-4 statistics-content">
          <!-- 概览卡片区域 -->
          <div class="overview-section">
            <v-row>
              <v-col v-for="(stat, index) in overviewStats" :key="index" cols="12" sm="6" md="3">
                <v-card
                  class="overview-card"
                  :color="stat.color"
                  rounded="lg"
                  elevation="3"
                  hover
                >
                  <v-card-text class="d-flex align-center pa-4 white--text">
                    <div class="stat-icon" :class="`stat-${index + 1}`">
                      <v-icon color="white" size="32">{{ stat.icon }}</v-icon>
                    </div>
                    <div class="ml-4">
                      <div class="text-h4 font-weight-bold">{{ stat.value }}</div>
                      <div class="text-body-2">{{ stat.label }}</div>
                      <div class="d-flex align-center mt-1">
                        <v-icon size="small" :color="stat.trend === 'up' ? 'light-green-accent-4' : 'red-accent-2'">
                          {{ stat.trend === 'up' ? 'mdi-arrow-up' : 'mdi-arrow-down' }}
                        </v-icon>
                        <span class="text-caption ml-1" :class="stat.trend === 'up' ? 'light-green-accent-4--text' : 'red-accent-2--text'">
                          {{ stat.change }}
                        </span>
                      </div>
                    </div>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>
          </div>
          
          <!-- 图表区域 -->
          <div class="charts-section mt-6">
            <v-row>
              <!-- 学生活跃度趋势图 -->
              <v-col cols="12" md="8">
                <v-card class="chart-card" elevation="2" rounded="lg">
                  <v-card-title class="chart-title py-3 px-6">
                    <v-icon color="primary" class="mr-2">mdi-chart-line</v-icon>
                    学生活跃度趋势
                    <v-spacer></v-spacer>
                    <v-btn-toggle
                      v-model="activityTimeRange"
                      mandatory
                      density="compact"
                      color="primary"
                      variant="outlined"
                    >
                      <v-btn value="week">
                        周
                      </v-btn>
                      <v-btn value="month">
                        月
                      </v-btn>
                    </v-btn-toggle>
                  </v-card-title>
                  <v-divider></v-divider>
                  <v-card-text class="pa-4">
                    <div ref="activeStudentsChart" class="chart-container"></div>
                  </v-card-text>
                </v-card>
              </v-col>
              
              <!-- 学习时长分布饼图 -->
              <v-col cols="12" md="4">
                <v-card class="chart-card" elevation="2" rounded="lg">
                  <v-card-title class="chart-title py-3 px-6">
                    <v-icon color="primary" class="mr-2">mdi-chart-pie</v-icon>
                    学习时长分布
                  </v-card-title>
                  <v-divider></v-divider>
                  <v-card-text class="pa-4">
                    <div ref="studyTimeChart" class="chart-container"></div>
                  </v-card-text>
                </v-card>
              </v-col>
              
              <!-- 视频观看排行 -->
              <v-col cols="12" md="6">
                <v-card class="chart-card" elevation="2" rounded="lg">
                  <v-card-title class="chart-title py-3 px-6">
                    <v-icon color="primary" class="mr-2">mdi-video</v-icon>
                    视频观看排行
                  </v-card-title>
                  <v-divider></v-divider>
                  <v-card-text class="pa-4">
                    <div ref="videoViewsChart" class="chart-container"></div>
                  </v-card-text>
                </v-card>
              </v-col>
              
              <!-- 课程完成率雷达图 -->
              <v-col cols="12" md="6">
                <v-card class="chart-card" elevation="2" rounded="lg">
                  <v-card-title class="chart-title py-3 px-6">
                    <v-icon color="primary" class="mr-2">mdi-radar</v-icon>
                    课程完成率分析
                  </v-card-title>
                  <v-divider></v-divider>
                  <v-card-text class="pa-4">
                    <div ref="courseCompletionChart" class="chart-container"></div>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>
          </div>
          
          <!-- 学生学习情况表格 -->
          <div class="data-tables-section mt-6">
            <v-card elevation="2" rounded="lg">
              <v-card-title class="py-3 px-6">
                <v-icon color="primary" class="mr-2">mdi-account-group</v-icon>
                学生学习情况
                <v-spacer></v-spacer>
                <v-text-field
                  v-model="search"
                  append-inner-icon="mdi-magnify"
                  label="搜索学生"
                  single-line
                  hide-details
                  density="compact"
                  style="max-width: 300px;"
                ></v-text-field>
              </v-card-title>
              <v-divider></v-divider>
              <v-card-text class="pa-0">
                <v-data-table
                  :headers="studentHeaders"
                  :items="studentData"
                  :search="search"
                  :items-per-page="5"
                  hover
                  class="student-table"
                >
                  <template v-slot:item.progress="{ item }">
                    <v-progress-linear
                      :model-value="item.progress"
                      color="primary"
                      height="12"
                      rounded
                      striped
                    >
                      <template v-slot:default="{ value }">
                        <span class="progress-text">{{ Math.ceil(value) }}%</span>
                      </template>
                    </v-progress-linear>
                  </template>
                  
                  <template v-slot:item.lastActive="{ item }">
                    <span :class="getActivityClass(item.lastActive)">{{ item.lastActive }}</span>
                  </template>
                  
                  <template v-slot:item.actions="{ item }">
                    <v-btn
                      icon
                      variant="text"
                      size="small"
                      color="primary"
                      @click="viewStudentDetails(item)"
                    >
                      <v-icon>mdi-eye</v-icon>
                    </v-btn>
                  </template>
                </v-data-table>
              </v-card-text>
            </v-card>
          </div>
        </v-card-text>
      </v-card>
    </v-container>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue';
import * as echarts from 'echarts';
import courseService from '../../api/courseService';
import { useRouter } from 'vue-router';

// 不需要单独注册组件，echarts已经包含所有必要组件

const router = useRouter();
const activeStudentsChart = ref(null);
const studyTimeChart = ref(null);
const videoViewsChart = ref(null);
const courseCompletionChart = ref(null);
const search = ref('');
const loading = ref(false);
const selectedCourse = ref('all');
const timePeriod = ref('month');
const activityTimeRange = ref('week');

// 图表实例引用
const chartsInstances = {
  activeStudents: null,
  studyTime: null,
  videoViews: null,
  courseCompletion: null
};

// 模拟数据 - 课程下拉选项
const courses = ref([
  { id: 'all', name: '全部课程' },
  { id: '1', name: '数据结构与算法' },
  { id: '2', name: '计算机组成原理' },
  { id: '3', name: 'Java编程基础' },
  { id: '4', name: 'Web前端开发' }
]);

// 时间周期选项
const timePeriods = [
  { value: 'week', title: '本周' },
  { value: 'month', title: '本月' },
  { value: 'semester', title: '本学期' }
];

// 模拟数据 - 总览统计
const overviewStats = ref([
  {
    label: '总学生人数',
    value: '256',
    icon: 'mdi-account-group',
    color: 'indigo',
    trend: 'up',
    change: '12% 增长',
  },
  {
    label: '活跃学生',
    value: '183',
    icon: 'mdi-account-check',
    color: 'teal',
    trend: 'up',
    change: '8% 增长',
  },
  {
    label: '视频观看次数',
    value: '1,354',
    icon: 'mdi-video-outline',
    color: 'deep-purple',
    trend: 'up',
    change: '24% 增长',
  },
  {
    label: '平均课程完成率',
    value: '76%',
    icon: 'mdi-check-circle-outline',
    color: 'amber darken-2',
    trend: 'down',
    change: '3% 下降',
  }
]);

// 模拟数据 - 学生学习情况表格
const studentHeaders = [
  { title: '学生姓名', key: 'name', align: 'start', sortable: true },
  { title: '学号', key: 'studentId', align: 'start', sortable: true },
  { title: '课程进度', key: 'progress', align: 'center', sortable: true },
  { title: '视频完成数', key: 'completedVideos', align: 'center', sortable: true },
  { title: '平均观看时长', key: 'avgWatchTime', align: 'center', sortable: true },
  { title: '最近活跃', key: 'lastActive', align: 'center', sortable: true },
  { title: '操作', key: 'actions', align: 'center', sortable: false }
];

const studentData = ref([
  { 
    id: '1', 
    name: '张三', 
    studentId: '2023001', 
    progress: 87, 
    completedVideos: 18, 
    avgWatchTime: '45分钟',
    lastActive: '今天' 
  },
  { 
    id: '2', 
    name: '李四', 
    studentId: '2023002', 
    progress: 65, 
    completedVideos: 13, 
    avgWatchTime: '32分钟',
    lastActive: '昨天' 
  },
  { 
    id: '3', 
    name: '王五', 
    studentId: '2023003', 
    progress: 92, 
    completedVideos: 20, 
    avgWatchTime: '57分钟',
    lastActive: '今天' 
  },
  { 
    id: '4', 
    name: '赵六', 
    studentId: '2023004', 
    progress: 45, 
    completedVideos: 9, 
    avgWatchTime: '23分钟',
    lastActive: '3天前' 
  },
  { 
    id: '5', 
    name: '钱七', 
    studentId: '2023005', 
    progress: 78, 
    completedVideos: 16, 
    avgWatchTime: '38分钟',
    lastActive: '今天' 
  },
  { 
    id: '6', 
    name: '孙八', 
    studentId: '2023006', 
    progress: 33, 
    completedVideos: 7, 
    avgWatchTime: '15分钟',
    lastActive: '1周前' 
  },
  { 
    id: '7', 
    name: '周九', 
    studentId: '2023007', 
    progress: 59, 
    completedVideos: 12, 
    avgWatchTime: '29分钟',
    lastActive: '2天前' 
  }
]);

// 根据最近活跃时间设置样式
const getActivityClass = (lastActive) => {
  if (lastActive === '今天') return 'green--text';
  if (lastActive === '昨天') return 'blue--text';
  if (lastActive.includes('天前') && parseInt(lastActive) <= 3) return 'orange--text';
  return 'grey--text';
};

// 查看学生详情
const viewStudentDetails = (item) => {
  router.push(`/students/details/${item.id}`);
};

// 初始化学生活跃度趋势图表
const initActiveStudentsChart = () => {
  if (!activeStudentsChart.value) return;
  
  // 销毁已有实例
  if (chartsInstances.activeStudents) {
    chartsInstances.activeStudents.dispose();
  }
  
  // 创建图表实例
  chartsInstances.activeStudents = echarts.init(activeStudentsChart.value);
  
  // 模拟数据
  const weekData = {
    xAxis: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
    series: [
      {
        name: '活跃学生数',
        data: [120, 132, 101, 134, 90, 70, 85]
      },
      {
        name: '视频观看次数',
        data: [220, 182, 191, 234, 290, 130, 150]
      }
    ]
  };
  
  const monthData = {
    xAxis: Array.from({length: 30}, (_, i) => `${i+1}日`),
    series: [
      {
        name: '活跃学生数',
        data: Array.from({length: 30}, () => Math.floor(Math.random() * 100 + 50))
      },
      {
        name: '视频观看次数',
        data: Array.from({length: 30}, () => Math.floor(Math.random() * 200 + 100))
      }
    ]
  };
  
  const data = activityTimeRange.value === 'week' ? weekData : monthData;
  
  // 配置选项
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    legend: {
      data: ['活跃学生数', '视频观看次数'],
      top: 'bottom'
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '10%',
      top: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: data.xAxis,
      axisTick: {
        alignWithLabel: true
      }
    },
    yAxis: [
      {
        type: 'value',
        name: '人数',
        position: 'left',
        axisLine: {
          show: true,
          lineStyle: {
            color: '#5470C6'
          }
        },
        axisLabel: {
          formatter: '{value}'
        }
      },
      {
        type: 'value',
        name: '次数',
        position: 'right',
        axisLine: {
          show: true,
          lineStyle: {
            color: '#91CC75'
          }
        },
        axisLabel: {
          formatter: '{value}'
        }
      }
    ],
    series: [
      {
        name: '活跃学生数',
        type: 'bar',
        data: data.series[0].data,
        itemStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: '#5470C6' },
              { offset: 1, color: '#91CC75' }
            ]
          }
        },
        yAxisIndex: 0,
        barWidth: activityTimeRange.value === 'week' ? '40%' : '60%'
      },
      {
        name: '视频观看次数',
        type: 'line',
        smooth: true,
        data: data.series[1].data,
        itemStyle: {
          color: '#EE6666'
        },
        yAxisIndex: 1
      }
    ],
    animationDuration: 1500
  };
  
  // 设置选项并渲染图表
  chartsInstances.activeStudents.setOption(option);
};

// 初始化学习时长分布饼图
const initStudyTimeChart = () => {
  if (!studyTimeChart.value) return;
  
  // 销毁已有实例
  if (chartsInstances.studyTime) {
    chartsInstances.studyTime.dispose();
  }
  
  // 创建图表实例
  chartsInstances.studyTime = echarts.init(studyTimeChart.value);
  
  // 配置选项
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'horizontal',
      bottom: 'bottom',
      data: ['<30分钟', '30-60分钟', '1-2小时', '2-3小时', '>3小时']
    },
    series: [
      {
        name: '学习时长分布',
        type: 'pie',
        radius: ['50%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: false,
          position: 'center'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: '18',
            fontWeight: 'bold'
          }
        },
        labelLine: {
          show: false
        },
        data: [
          { value: 35, name: '<30分钟' },
          { value: 45, name: '30-60分钟' },
          { value: 68, name: '1-2小时' },
          { value: 42, name: '2-3小时' },
          { value: 28, name: '>3小时' }
        ],
        animationType: 'scale',
        animationEasing: 'elasticOut',
        animationDelay: function (idx) {
          return idx * 200;
        }
      }
    ]
  };
  
  // 设置选项并渲染图表
  chartsInstances.studyTime.setOption(option);
};

// 初始化视频观看排行图表
const initVideoViewsChart = () => {
  if (!videoViewsChart.value) return;
  
  // 销毁已有实例
  if (chartsInstances.videoViews) {
    chartsInstances.videoViews.dispose();
  }
  
  // 创建图表实例
  chartsInstances.videoViews = echarts.init(videoViewsChart.value);
  
  // 配置选项
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      boundaryGap: [0, 0.01]
    },
    yAxis: {
      type: 'category',
      data: [
        '第一章：课程介绍',
        '第二章：基础概念',
        '第三章：进阶技巧',
        '第四章：实战应用',
        '第五章：设计模式',
        '第六章：最佳实践',
        '第七章：总结展望'
      ].reverse(),
      axisLabel: {
        formatter: function (value) {
          if (value.length > 10) {
            return value.substring(0, 10) + '...';
          }
          return value;
        }
      }
    },
    series: [
      {
        name: '观看次数',
        type: 'bar',
        data: [235, 210, 198, 175, 142, 98, 76].reverse(),
        itemStyle: {
          color: {
            type: 'linear',
            x: 1, y: 0, x2: 0, y2: 0,
            colorStops: [
              { offset: 0, color: '#6f23d1' },
              { offset: 0.5, color: '#a35eea' },
              { offset: 1, color: '#d49fff' }
            ]
          }
        },
        label: {
          show: true,
          position: 'right',
          formatter: '{c} 次'
        },
        animationDelay: function (idx) {
          return idx * 100 + 100;
        }
      }
    ],
    animationEasing: 'elasticOut',
    animationDelayUpdate: function (idx) {
      return idx * 5;
    }
  };
  
  // 设置选项并渲染图表
  chartsInstances.videoViews.setOption(option);
};

// 初始化课程完成率雷达图
const initCourseCompletionChart = () => {
  if (!courseCompletionChart.value) return;
  
  // 销毁已有实例
  if (chartsInstances.courseCompletion) {
    chartsInstances.courseCompletion.dispose();
  }
  
  // 创建图表实例
  chartsInstances.courseCompletion = echarts.init(courseCompletionChart.value);
  
  // 配置选项
  const option = {
    tooltip: {
      trigger: 'item'
    },
    legend: {
      type: 'scroll',
      bottom: 'bottom',
      data: ['优秀学生', '平均水平', '需要关注']
    },
    radar: {
      indicator: [
        { name: '视频完成率', max: 100 },
        { name: '作业提交率', max: 100 },
        { name: '考试通过率', max: 100 },
        { name: '互动参与度', max: 100 },
        { name: '资料下载率', max: 100 }
      ],
      radius: '65%',
      center: ['50%', '50%'],
      shape: 'circle',
      splitNumber: 5,
      axisName: {
        color: 'rgb(102, 102, 102)'
      },
      splitLine: {
        lineStyle: {
          color: [
            'rgba(238, 197, 102, 0.1)',
            'rgba(238, 197, 102, 0.2)',
            'rgba(238, 197, 102, 0.4)',
            'rgba(238, 197, 102, 0.6)',
            'rgba(238, 197, 102, 0.8)',
            'rgba(238, 197, 102, 1)'
          ].reverse()
        }
      },
      splitArea: {
        show: false
      },
      axisLine: {
        lineStyle: {
          color: 'rgba(238, 197, 102, 0.5)'
        }
      }
    },
    series: [
      {
        name: '课程完成率分布',
        type: 'radar',
        emphasis: {
          lineStyle: {
            width: 4
          }
        },
        data: [
          {
            value: [90, 95, 85, 80, 88],
            name: '优秀学生',
            symbol: 'circle',
            symbolSize: 8,
            lineStyle: {
              width: 2,
              type: 'solid'
            },
            areaStyle: {
              opacity: 0.3
            }
          },
          {
            value: [75, 70, 72, 65, 78],
            name: '平均水平',
            symbol: 'rect',
            symbolSize: 6,
            lineStyle: {
              width: 2,
              type: 'dashed'
            },
            areaStyle: {
              opacity: 0.3
            }
          },
          {
            value: [40, 45, 35, 30, 50],
            name: '需要关注',
            symbol: 'triangle',
            symbolSize: 6,
            lineStyle: {
              width: 2,
              type: 'dotted'
            },
            areaStyle: {
              opacity: 0.3
            }
          }
        ]
      }
    ],
    animationDuration: 1500
  };
  
  // 设置选项并渲染图表
  chartsInstances.courseCompletion.setOption(option);
};

// 加载统计数据
const loadStatistics = async () => {
  loading.value = true;
  
  try {
    // 调用统计数据API
    const response = await courseService.getStatisticsOverview({
      course_id: selectedCourse.value,
      time_period: timePeriod.value
    });
    
    if (response.data.code === 200) {
      const data = response.data.data;
      
      // 更新总览统计数据
      overviewStats.value = data.overview_stats || [];
      
      // 更新学生数据
      studentData.value = data.student_data || [];
      
      // 更新课程选项（仅首次加载时更新）
      if (data.courses && courses.value.length <= 1) {
        courses.value = data.courses;
      }
      
      // 等待DOM更新后再初始化图表
      await nextTick();
      
      // 更新图表数据
      updateChartsWithRealData(data);
    } else {
      console.error('API响应失败:', response.data.message);
      initAllCharts();
    }
    
  } catch (error) {
    console.error('加载统计数据失败:', error);
    // 如果API调用失败，使用模拟数据
    initAllCharts();
  } finally {
    loading.value = false;
  }
};

// 使用真实数据更新图表
const updateChartsWithRealData = (data) => {
  // 更新活跃学生趋势图
  if (data.trend_data && data.trend_data.length > 0) {
    updateActiveStudentsChart(data.trend_data);
  } else {
    initActiveStudentsChart();
  }
  
  // 更新学习时长分布图
  if (data.study_time_distribution) {
    updateStudyTimeChart(data.study_time_distribution);
  } else {
    initStudyTimeChart();
  }
  
  // 更新视频观看排行图
  if (data.video_ranking) {
    updateVideoViewsChart(data.video_ranking);
  } else {
    initVideoViewsChart();
  }
  
  // 更新课程完成率雷达图
  if (data.course_completion_radar) {
    updateCourseCompletionChart(data.course_completion_radar);
  } else {
    initCourseCompletionChart();
  }
};

// 使用真实数据更新活跃学生图表
const updateActiveStudentsChart = (trendData) => {
  if (!activeStudentsChart.value) return;
  
  if (chartsInstances.activeStudents) {
    chartsInstances.activeStudents.dispose();
  }
  
  chartsInstances.activeStudents = echarts.init(activeStudentsChart.value);
  
  const xAxisData = trendData.map(item => item.date.substring(5)); // 只显示月-日
  const activeStudentsData = trendData.map(item => item.active_students);
  const videoViewsData = trendData.map(item => item.video_views);
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    legend: {
      data: ['活跃学生数', '视频观看次数'],
      top: 'bottom'
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '10%',
      top: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: xAxisData,
      axisTick: {
        alignWithLabel: true
      }
    },
    yAxis: [
      {
        type: 'value',
        name: '人数',
        position: 'left',
        axisLine: {
          show: true,
          lineStyle: {
            color: '#5470C6'
          }
        }
      },
      {
        type: 'value',
        name: '次数',
        position: 'right',
        axisLine: {
          show: true,
          lineStyle: {
            color: '#91CC75'
          }
        }
      }
    ],
    series: [
      {
        name: '活跃学生数',
        type: 'bar',
        data: activeStudentsData,
        itemStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: '#5470C6' },
              { offset: 1, color: '#91CC75' }
            ]
          }
        },
        yAxisIndex: 0
      },
      {
        name: '视频观看次数',
        type: 'line',
        smooth: true,
        data: videoViewsData,
        itemStyle: {
          color: '#EE6666'
        },
        yAxisIndex: 1
      }
    ],
    animationDuration: 1500
  };
  
  chartsInstances.activeStudents.setOption(option);
};

// 使用真实数据更新学习时长分布图
const updateStudyTimeChart = (distributionData) => {
  if (!studyTimeChart.value) return;
  
  if (chartsInstances.studyTime) {
    chartsInstances.studyTime.dispose();
  }
  
  chartsInstances.studyTime = echarts.init(studyTimeChart.value);
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'horizontal',
      bottom: 'bottom',
      data: distributionData.map(item => item.name)
    },
    series: [
      {
        name: '学习时长分布',
        type: 'pie',
        radius: ['50%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: false,
          position: 'center'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: '18',
            fontWeight: 'bold'
          }
        },
        labelLine: {
          show: false
        },
        data: distributionData,
        animationType: 'scale',
        animationEasing: 'elasticOut',
        animationDelay: function (idx) {
          return idx * 200;
        }
      }
    ]
  };
  
  chartsInstances.studyTime.setOption(option);
};

// 使用真实数据更新视频观看排行图
const updateVideoViewsChart = (rankingData) => {
  if (!videoViewsChart.value) return;
  
  if (chartsInstances.videoViews) {
    chartsInstances.videoViews.dispose();
  }
  
  chartsInstances.videoViews = echarts.init(videoViewsChart.value);
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      boundaryGap: [0, 0.01]
    },
    yAxis: {
      type: 'category',
      data: rankingData.map(item => item.name).reverse(),
      axisLabel: {
        formatter: function (value) {
          if (value.length > 10) {
            return value.substring(0, 10) + '...';
          }
          return value;
        }
      }
    },
    series: [
      {
        name: '观看次数',
        type: 'bar',
        data: rankingData.map(item => item.views).reverse(),
        itemStyle: {
          color: {
            type: 'linear',
            x: 1, y: 0, x2: 0, y2: 0,
            colorStops: [
              { offset: 0, color: '#6f23d1' },
              { offset: 0.5, color: '#a35eea' },
              { offset: 1, color: '#d49fff' }
            ]
          }
        },
        label: {
          show: true,
          position: 'right',
          formatter: '{c} 次'
        },
        animationDelay: function (idx) {
          return idx * 100 + 100;
        }
      }
    ],
    animationEasing: 'elasticOut'
  };
  
  chartsInstances.videoViews.setOption(option);
};

// 使用真实数据更新课程完成率雷达图
const updateCourseCompletionChart = (radarData) => {
  if (!courseCompletionChart.value) return;
  
  if (chartsInstances.courseCompletion) {
    chartsInstances.courseCompletion.dispose();
  }
  
  chartsInstances.courseCompletion = echarts.init(courseCompletionChart.value);
  
  const indicators = radarData.map(item => ({
    name: item.name,
    max: 100
  }));
  
  const seriesData = radarData.map(item => item.value);
  
  const option = {
    tooltip: {
      trigger: 'item'
    },
    radar: {
      indicator: indicators,
      shape: 'polygon',
      startAngle: 90,
      splitNumber: 4,
      splitArea: {
        areaStyle: {
          color: ['rgba(114, 172, 209, 0.2)', 'rgba(114, 172, 209, 0.4)',
                  'rgba(114, 172, 209, 0.6)', 'rgba(114, 172, 209, 0.8)',
                  'rgba(114, 172, 209, 1)']
        }
      },
      axisLine: {
        lineStyle: {
          color: 'rgba(114, 172, 209, 0.2)'
        }
      },
      splitLine: {
        lineStyle: {
          color: 'rgba(114, 172, 209, 0.5)'
        }
      }
    },
    series: [
      {
        name: '课程完成率',
        type: 'radar',
        data: [
          {
            value: seriesData,
            name: '完成率',
            symbol: 'circle',
            symbolSize: 8,
            lineStyle: {
              width: 2,
              type: 'solid'
            },
            areaStyle: {
              opacity: 0.3
            }
          }
        ]
      }
    ],
    animationDuration: 1500
  };
  
  chartsInstances.courseCompletion.setOption(option);
};

// 刷新数据
const refreshData = () => {
  loadStatistics();
};

// 初始化所有图表
const initAllCharts = () => {
  initActiveStudentsChart();
  initStudyTimeChart();
  initVideoViewsChart();
  initCourseCompletionChart();
};

// 监听时间范围变化，更新活跃度图表
watch(activityTimeRange, () => {
  initActiveStudentsChart();
});

// 监听窗口大小变化，调整图表大小
const handleResize = () => {
  Object.values(chartsInstances).forEach(chart => {
    chart && chart.resize();
  });
};

// 加载教师课程列表
const loadTeacherCourses = async () => {
  try {
    const response = await courseService.getTeacherCourses();
    if (response.data.success) {
      courses.value = response.data.data;
    }
  } catch (error) {
    console.error('加载课程列表失败:', error);
  }
};

// 生命周期钩子
onMounted(async () => {
  // 先加载课程列表
  await loadTeacherCourses();
  
  // 等待DOM更新
  await nextTick();
  
  // 初始化图表
  setTimeout(() => {
    initAllCharts();
  }, 100);
  
  // 添加窗口大小变化监听
  window.addEventListener('resize', handleResize);
  
  // 加载统计数据
  loadStatistics();
});

onBeforeUnmount(() => {
  // 移除窗口大小变化监听
  window.removeEventListener('resize', handleResize);
  
  // 销毁所有图表实例
  Object.values(chartsInstances).forEach(chart => {
    chart && chart.dispose();
  });
});
</script>

<style scoped>
.statistics-view {
  height: 100%;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.content-card {
  height: 100%;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.content-card > .v-card-text {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.statistics-content {
  flex: 1;
  overflow-y: auto;
}

.overview-card {
  transition: transform 0.3s, box-shadow 0.3s;
  border-radius: 12px;
  overflow: hidden;
}

.overview-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
}

.stat-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.2);
}

.chart-card {
  height: 100%;
  border-radius: 12px;
  overflow: hidden;
  transition: transform 0.3s, box-shadow 0.3s;
}

.chart-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1);
}

.chart-container {
  width: 100%;
  height: 350px;
}

.chart-title {
  font-weight: 500;
}

.trend.up {
  color: #4caf50;
}

.trend.down {
  color: #f44336;
}

.student-table {
  border-radius: 0 0 12px 12px;
  overflow: hidden;
}

.student-table :deep(.v-data-table) {
  max-height: 400px;
  overflow-y: auto;
}

.progress-text {
  color: white;
  font-size: 0.75rem;
  font-weight: 500;
}

/* 手机端适配 */
@media (max-width: 960px) {
  .chart-container {
    height: 300px;
  }
  
  .overview-section .v-col {
    padding: 8px;
  }
}

@media (max-width: 600px) {
  .chart-container {
    height: 250px;
  }
  
  .stat-icon {
    width: 48px;
    height: 48px;
  }
}

/* 添加动画效果 */
.overview-card {
  animation: fadeInUp 0.5s ease-out;
}

.chart-card {
  animation: fadeIn 0.8s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.stat-1 {
  animation-delay: 0.1s;
}

.stat-2 {
  animation-delay: 0.2s;
}

.stat-3 {
  animation-delay: 0.3s;
}

.stat-4 {
  animation-delay: 0.4s;
}
</style> 