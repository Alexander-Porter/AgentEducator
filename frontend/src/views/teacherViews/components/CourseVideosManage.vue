<template>
  <v-container fluid class="pa-4">
    <v-card class="content-card">      <v-card-title class="d-flex align-center py-4 px-6">
        课程视频管理
        <v-tooltip location="top">
          <template v-slot:activator="{ props }">
            <v-btn icon variant="text" v-bind="props" class="ms-2">
              <v-icon>mdi-information-outline</v-icon>
            </v-btn>
          </template>
          <span>管理课程关联的视频，可以重命名、删除或添加视频</span>
        </v-tooltip>
        <v-spacer></v-spacer>        <v-text-field
          v-model="searchQuery"
          prepend-inner-icon="mdi-magnify"
          label="搜索视频..."
          single-line
          hide-details
          density="compact"
          class="search-field me-4"
          clear-icon="mdi-close-circle"
          clearable
          @update:model-value="filterVideos"
        ></v-text-field>        <v-btn
          color="primary"
          prepend-icon="mdi-upload"
          @click="navigateToUpload"
          class="me-2"
        >
          上传视频
        </v-btn>        <v-btn
          color="success"
          prepend-icon="mdi-graph-outline"
          @click="generateKnowledgeGraph"
          class="me-2"
          :loading="knowledgeGraphLoading"
        >
          生成知识图谱
        </v-btn>
        <v-menu v-if="selectedVideos.length > 0">
          <template v-slot:activator="{ props }">
            <v-btn
              color="secondary"
              prepend-icon="mdi-dots-vertical"
              v-bind="props"
            >
              批量操作 ({{ selectedVideos.length }})
            </v-btn>
          </template>
          <v-list>
            <v-list-item @click="confirmBatchProcess">
              <template v-slot:prepend>
                <v-icon>mdi-cog</v-icon>
              </template>
              <v-list-item-title>批量处理</v-list-item-title>
            </v-list-item>
            <v-list-item @click="confirmBatchDelete">
              <template v-slot:prepend>
                <v-icon>mdi-link-off</v-icon>
              </template>
              <v-list-item-title>批量解除关联</v-list-item-title>
            </v-list-item>
          </v-list>
        </v-menu>
      </v-card-title>
      <v-divider></v-divider>
      
      <v-card-text class="pa-4 scrollable-content">
        <!-- 加载状态 -->
        <div v-if="loading" class="d-flex justify-center align-center pa-8">
          <v-progress-circular indeterminate color="primary"></v-progress-circular>
          <span class="ms-4">加载视频数据中...</span>
        </div>
        
        <!-- 视频列表 -->
        <div v-else>
          <!-- 视频总数和全选 -->
          <div class="d-flex align-center mb-4">
            <div class="text-body-1 flex-grow-1">
              共找到 <b>{{ filteredVideos.length }}</b> 个视频
            </div>
            <v-checkbox
              v-if="filteredVideos.length > 0"
              v-model="selectAll"
              label="全选"
              hide-details
              density="compact"
              @change="handleSelectAll"
            ></v-checkbox>
          </div>
          
          <!-- 视频列表 - 网格布局 -->
          <v-row v-if="filteredVideos.length > 0">
            <v-col
              v-for="video in filteredVideos"
              :key="video.id"
              cols="12"
              sm="6"
              md="4"
              lg="3"
            >              <v-card class="video-card" :class="{'selected': isVideoSelected(video.id)}">
                <div class="video-thumbnail">
                  <v-checkbox
                    v-model="selectedVideos"
                    :value="video.id"
                    hide-details
                    density="compact"
                    class="video-checkbox ma-2"
                  ></v-checkbox>
                  <v-img
                    :src="video.coverUrl || 'https://picsum.photos/400/225?random=' + video.id"
                    aspect-ratio="16/9"
                    cover
                    @click="toggleVideoSelection(video.id)"
                  >
                    <div class="video-duration">{{ formatDuration(video.duration) }}</div>
                  </v-img>
                </div>
                
                <v-card-item>
                  <v-card-title class="text-subtitle-1">{{ video.title }}</v-card-title>
                  <v-card-subtitle class="text-caption">
                    上传于: {{ formatDate(video.uploadTime) }}
                  </v-card-subtitle>
                </v-card-item>
                
                <v-card-text class="px-4 pb-0">                  <div class="d-flex mb-2">
                    <v-icon size="small" class="me-1">mdi-eye</v-icon>
                    <span class="text-body-2 me-3">{{ video.viewCount }}次观看</span>
                    <v-icon size="small" class="me-1">mdi-comment-outline</v-icon>
                    <span class="text-body-2">{{ video.commentCount }}条评论</span>
                  </div>
                  <div class="text-caption text-truncate-2">{{ video.description }}</div>
                </v-card-text>
                
                <v-card-actions class="pa-4">
                  <v-btn variant="text" @click="showVideoDetails(video)">
                    <v-icon>mdi-eye</v-icon>
                    查看
                  </v-btn>
                  <v-spacer></v-spacer>
                  <v-btn icon variant="text" @click="showRenameDialog(video)">
                    <v-icon>mdi-pencil</v-icon>
                  </v-btn>
                  <v-btn icon variant="text" color="warning" @click="processVideo(video)">
                    <v-icon>mdi-cog</v-icon>
                  </v-btn>
                  <v-btn icon variant="text" @click="confirmDeleteVideo(video)">
                    <v-icon>mdi-link-off</v-icon>
                  </v-btn>
                </v-card-actions>
              </v-card>
            </v-col>
          </v-row>
          
          <!-- 空状态 -->
          <v-row v-else class="fill-height align-center justify-center">
            <v-col cols="12" class="text-center pa-12">
              <v-icon size="64" color="grey">mdi-video-off</v-icon>
              <div class="text-h6 mt-4 text-grey">暂无视频</div>
              <div class="text-body-1 mt-2 text-grey">
                您可以点击"上传视频"按钮为本课程添加视频
              </div>
              <v-btn
                color="primary"
                class="mt-4"
                @click="navigateToUpload"
              >
                上传视频
              </v-btn>
            </v-col>
          </v-row>
        </div>
      </v-card-text>
    </v-card>
    
    <!-- 重命名对话框 -->
    <v-dialog v-model="showRenameModal" max-width="500">
      <v-card>
        <v-card-title class="text-h5 pa-4">
          重命名视频
          <v-spacer></v-spacer>
          <v-btn icon @click="closeRenameDialog">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text class="pa-4">
          <v-form ref="renameForm">
            <v-text-field
              v-model="videoEdit.title"
              label="视频标题"
              variant="outlined"
              density="comfortable"
              class="mb-4"
              required
            ></v-text-field>
            <v-textarea
              v-model="videoEdit.description"
              label="视频描述"
              variant="outlined"
              density="comfortable"
              rows="4"
            ></v-textarea>
          </v-form>
        </v-card-text>
        <v-divider></v-divider>
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="closeRenameDialog">取消</v-btn>
          <v-btn color="primary" @click="saveVideoInfo">保存</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
      <!-- 删除确认对话框 -->
    <v-dialog v-model="showDeleteModal" max-width="400">
      <v-card>
        <v-card-title class="text-h5 pa-4">
          解除视频关联
          <v-spacer></v-spacer>
          <v-btn icon @click="closeDeleteDialog">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-card-text class="pa-4 text-center">
          <v-icon
            color="warning"
            size="64"
            class="mb-4"
          >
            mdi-alert-circle
          </v-icon>
          <div class="text-body-1">
            您确定要解除视频 <strong>{{ videoToDelete?.title }}</strong> 与该课程的关联吗？
          </div>
          <div class="text-caption text-warning mt-2">
            注意：如果该视频不再与任何课程关联，系统将会删除视频文件。
          </div>
        </v-card-text>
        <v-divider></v-divider>
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="closeDeleteDialog">取消</v-btn>
          <v-btn color="error" @click="deleteVideo">解除关联</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    
    <!-- 批量删除确认对话框 -->
    <v-dialog v-model="showBatchDeleteModal" max-width="500">
      <v-card>
        <v-card-title class="text-h5 pa-4">
          批量解除视频关联
          <v-spacer></v-spacer>
          <v-btn icon @click="closeBatchDeleteDialog">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-card-text class="pa-4 text-center">
          <v-icon
            color="warning"
            size="64"
            class="mb-4"
          >
            mdi-alert-circle
          </v-icon>
          <div class="text-body-1">
            您确定要批量解除 <strong>{{ selectedVideos.length }}</strong> 个视频与该课程的关联吗？
          </div>
          <div class="text-caption text-warning mt-2">
            注意：如果这些视频不再与任何课程关联，系统将会删除相应视频文件。
          </div>
        </v-card-text>
        <v-divider></v-divider>
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="closeBatchDeleteDialog">取消</v-btn>
          <v-btn color="error" @click="batchDeleteVideos" :loading="batchProcessing">批量解除关联</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    
    <!-- 批量处理确认对话框 -->
    <v-dialog v-model="showBatchProcessModal" max-width="500">
      <v-card>
        <v-card-title class="text-h5 pa-4">
          批量处理视频
          <v-spacer></v-spacer>
          <v-btn icon @click="closeBatchProcessDialog">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-card-text class="pa-4 text-center">
          <v-icon
            color="info"
            size="64"
            class="mb-4"
          >
            mdi-cog
          </v-icon>          <div class="text-body-1">
            您确定要批量处理 <strong>{{ selectedVideos.length }}</strong> 个视频吗？
            <span v-if="searchQuery" class="text-caption d-block mt-1">
              (当前搜索筛选：{{ filteredVideos.filter(v => selectedVideos.includes(v.id)).length }} 个视频)
            </span>
          </div>
          <div class="text-caption mt-2">
            处理包括：提取关键帧、OCR文字识别、语音识别等步骤，可能需要一些时间。
          </div>          <v-alert
            v-if="selectedVideos.length > 10"
            type="warning"
            variant="tonal"
            class="mt-3"
            density="compact"
          >
            您选择了较多视频进行处理，处理过程可能需要一些时间，请耐心等待。
          </v-alert>
        </v-card-text>
        <v-divider></v-divider>
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="closeBatchProcessDialog">取消</v-btn>
          <v-btn color="primary" @click="batchProcessVideos" :loading="batchProcessing">
            开始处理
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
      <!-- 批量处理进度对话框 -->
    <v-dialog v-model="showBatchProgressModal" persistent max-width="500">
      <v-card>
        <v-card-title class="text-h5 pa-4">
          批量处理进度
        </v-card-title>
        <v-card-text class="pa-4">
          <div class="text-body-1 mb-2">
            已处理：{{ processedCount }}/{{ selectedVideos.length }} 个视频
          </div>
          <v-progress-linear
            v-model="batchProgress"
            height="20"
            color="primary"
            striped
          >
            <template v-slot:default>
              {{ Math.round(batchProgress) }}%
            </template>
          </v-progress-linear>
          
          <div class="mt-4">
            <div v-for="(status, index) in processingStatus" :key="index" class="d-flex align-center mb-1">
              <v-icon :color="status.color" size="small" class="me-2">{{ status.icon }}</v-icon>
              <span :class="{'text-caption': true, [status.textClass]: true}">{{ status.message }}</span>
            </div>
          </div>
        </v-card-text>
        <v-divider></v-divider>
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn color="primary" @click="closeBatchProgressDialog" :disabled="batchProcessing">
            {{ batchProcessing ? '处理中...' : '完成' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 强制重新生成知识图谱确认对话框 -->
    <v-dialog v-model="showForceRegenerateDialog" max-width="500">
      <v-card>
        <v-card-title class="text-h5 pa-4">
          知识图谱生成冲突
          <v-spacer></v-spacer>
          <v-btn icon @click="closeForceRegenerateDialog">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-card-text class="pa-4">
          <v-icon color="warning" size="64" class="mb-4 d-block mx-auto"></v-icon>
          <div class="text-center">
            <div class="text-body-1 mb-3">
              该课程已有知识图谱生成任务正在进行中
            </div>            <div v-if="pendingKnowledgeGraphTask" class="text-caption text-medium-emphasis mb-3">
              任务状态：{{ pendingKnowledgeGraphTask.status }}<br>
              开始时间：{{ formatDateTime(pendingKnowledgeGraphTask.start_time) }}<br>
              进度：{{ Math.round((pendingKnowledgeGraphTask.progress || 0) * 100) }}%
            </div>
            <div class="text-body-2">
              您可以选择等待当前任务完成，或强制重新生成（这将终止当前任务并删除已有的知识图谱数据）。
            </div>
          </div>
        </v-card-text>
        <v-divider></v-divider>
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="closeForceRegenerateDialog">
            等待完成
          </v-btn>          <v-btn color="warning" @click="forceRegenerateKnowledgeGraph" :loading="knowledgeGraphLoading">
            强制重新生成
          </v-btn>
        </v-card-actions>
      </v-card>    </v-dialog>

    <!-- 视频处理设置对话框 -->
    <v-dialog v-model="showProcessSettingsModal" max-width="600">
      <v-card>
        <v-card-title class="text-h5 pa-4">
          视频处理设置
          <v-spacer></v-spacer>
          <v-btn icon @click="closeProcessSettingsDialog">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text class="pa-4">
          <div v-if="processSettingsTarget === 'single'" class="mb-4">
            <div class="text-body-1 mb-2">视频: {{ currentProcessVideo?.title }}</div>
          </div>
          <div v-else class="mb-4">
            <div class="text-body-1 mb-2">批量处理 {{ selectedVideos.length }} 个视频</div>
          </div>

          <!-- 预览模式开关 -->
          <div class="mb-4">
            <v-switch
              v-model="processPreviewMode"
              color="primary"
              label="预览模式"
              hint="预览模式下将执行所有处理步骤但不保存到数据库，仅生成处理日志"
              persistent-hint
            ></v-switch>
          </div>

          <!-- 处理步骤选择 -->
          <div class="mb-4">
            <v-card-subtitle class="pa-0 mb-2">选择处理步骤</v-card-subtitle>
            <v-checkbox-group v-model="processSelectedSteps" column>
              <v-checkbox
                v-for="step in processingSteps"
                :key="step.value"
                :value="step.value"
                :label="step.label"
                :disabled="processPreviewMode"
                density="compact"
              >
                <template v-slot:label>
                  <div class="d-flex align-center">
                    <v-icon :icon="step.icon" class="mr-2" size="small"></v-icon>
                    <span>{{ step.label }}</span>
                    <v-tooltip activator="parent" location="top">
                      {{ step.description }}
                    </v-tooltip>
                  </div>
                </template>
              </v-checkbox>
            </v-checkbox-group>
            <v-card-text class="pa-0 text-caption text-medium-emphasis" v-if="!processPreviewMode">
              * 未选择步骤将跳过处理。已处理的步骤可以重新执行以更新数据。
            </v-card-text>
            <v-card-text class="pa-0 text-caption text-medium-emphasis" v-else>
              * 预览模式下将执行所有步骤
            </v-card-text>
          </div>

          <!-- 处理状态查询 -->
          <div v-if="processSettingsTarget === 'single' && currentProcessVideo" class="mb-4">
            <v-btn
              variant="outlined"
              size="small"
              prepend-icon="mdi-information"
              @click="checkVideoProcessingStatus"
              :loading="checkingStatus"
            >
              查看当前处理状态
            </v-btn>
            
            <div v-if="videoProcessingStatus" class="mt-3">
              <v-card variant="outlined" class="pa-3">
                <v-card-subtitle class="pa-0 mb-2">当前处理状态</v-card-subtitle>
                <div v-for="(status, stepName) in videoProcessingStatus" :key="stepName" class="d-flex align-center mb-1">
                  <v-icon 
                    :color="status ? 'success' : 'grey'" 
                    class="mr-2" 
                    size="small"
                  >
                    {{ status ? 'mdi-check-circle' : 'mdi-circle-outline' }}
                  </v-icon>
                  <span :class="status ? 'text-success' : 'text-medium-emphasis'">
                    {{ getStepDisplayName(stepName) }}
                  </span>
                </div>
              </v-card>
            </div>
          </div>
        </v-card-text>
        <v-divider></v-divider>
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="closeProcessSettingsDialog">取消</v-btn>
          <v-btn 
            color="primary" 
            @click="startProcessingWithSettings"
            :disabled="!processPreviewMode && processSelectedSteps.length === 0"
          >
            {{ processPreviewMode ? '开始预览' : '开始处理' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

  </v-container>
</template>

<script setup>
import { ref, computed, reactive, onMounted, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import videoService from '../../../api/videoService';
import knowledgeMapService from '../../../api/knowledgeMapService';

// 获取路由和参数
const router = useRouter();
const route = useRoute();
const courseId = ref(route.params.id || null); // 从路由参数获取课程ID

// 状态管理
const loading = ref(false);
const videos = ref([]);
const filteredVideos = ref([]);
const searchQuery = ref('');
const selectAll = ref(false);

// 视频编辑相关
const showRenameModal = ref(false);
const videoEdit = reactive({
  id: null,
  title: '',
  description: ''
});

// 视频删除相关
const showDeleteModal = ref(false);
const videoToDelete = ref(null);


const checkingStatus = ref(false);

// 批量选择相关
const selectedVideos = ref([]);
const showBatchDeleteModal = ref(false);
const showBatchProcessModal = ref(false);
const showBatchProgressModal = ref(false);
const batchProcessing = ref(false);
const batchProgress = ref(0);
const processedCount = ref(0);
const processingStatus = ref([]);

// 视频处理设置相关
const showProcessSettingsModal = ref(false);
const processSettingsTarget = ref('single'); // 'single' 或 'batch'
const currentProcessVideo = ref(null);
const processPreviewMode = ref(false);
const processSelectedSteps = ref(['keyframes', 'ocr', 'asr', 'vector', 'summary']);
const checkingStatus = ref(false);
const videoProcessingStatus = ref(null);

// 处理步骤选项
const processingSteps = ref([
  {
    value: 'keyframes',
    label: '关键帧提取',
    icon: 'mdi-image-multiple',
    description: '提取视频关键帧用于封面和缩略图生成'
  },
  {
    value: 'ocr',
    label: 'OCR文字识别',
    icon: 'mdi-text-recognition',
    description: '识别视频中的文字内容，生成文本索引'
  },
  {
    value: 'asr',
    label: 'ASR语音识别',
    icon: 'mdi-microphone',
    description: '将视频中的语音转换为文字，生成字幕'
  },
  {
    value: 'vector',
    label: '向量化处理',
    icon: 'mdi-vector-triangle',
    description: '将文本内容向量化，用于语义搜索和问答'
  },
  {
    value: 'summary',
    label: '智能摘要',
    icon: 'mdi-text-box-outline',
    description: '生成视频内容的智能摘要和关键词'
  }
]);

// 知识图谱相关
const knowledgeGraphLoading = ref(false);
const showForceRegenerateDialog = ref(false);
const pendingKnowledgeGraphTask = ref(null);
// 移除最大并发处理任务数限制
const processingInterval = ref(null); // 轮询间隔ID

// 视频选择状态处理
const isVideoSelected = (videoId) => {
  return selectedVideos.value.includes(videoId);
};

// 切换视频选择状态
const toggleVideoSelection = (videoId) => {
  const index = selectedVideos.value.indexOf(videoId);
  if (index === -1) {
    selectedVideos.value.push(videoId);
  } else {
    selectedVideos.value.splice(index, 1);
  }
};

// 全选/取消全选
const handleSelectAll = () => {
  if (selectAll.value) {
    // 全选当前筛选结果中的所有视频
    const filteredIds = filteredVideos.value.map(video => video.id);
    
    // 合并现有选择和筛选结果中的ID（去重）
    const existingSelectedIds = selectedVideos.value.filter(id => 
      !filteredVideos.value.some(video => video.id === id)
    );
    
    selectedVideos.value = [...existingSelectedIds, ...filteredIds];
  } else {
    // 仅从选择中移除当前筛选结果的视频
    if (searchQuery.value) {
      const filteredIds = filteredVideos.value.map(video => video.id);
      selectedVideos.value = selectedVideos.value.filter(id => !filteredIds.includes(id));
    } else {
      // 没有筛选时，取消所有选择
      selectedVideos.value = [];
    }
  }
};

// 监听选中视频变化，更新全选状态
watch(selectedVideos, (newVal) => {
  // 如果当前筛选结果中的所有视频都被选中，则全选为true，否则为false
  selectAll.value = filteredVideos.value.length > 0 && 
                    filteredVideos.value.every(video => selectedVideos.value.includes(video.id));
}, { deep: true });

// 监听筛选结果变化，可能需要重新计算全选状态
watch(filteredVideos, () => {
  // 如果当前筛选结果中的所有视频都被选中，则全选为true，否则为false
  selectAll.value = filteredVideos.value.length > 0 && 
                    filteredVideos.value.every(video => selectedVideos.value.includes(video.id));
}, { deep: true });

// 方法
// 获取视频列表
const fetchVideos = async () => {
  loading.value = true;
  
  try {
    const response = await videoService.getVideos({
      courseId: courseId.value,
      page: 1,
      pageSize: 100 // 设置一个较大的值，获取所有视频
    });
    
    if (response.data && response.data.code === 200) {
      videos.value = response.data.data.list || [];
      filterVideos(); // 初始化筛选结果
    } else {
      throw new Error(response.data.message || '获取视频列表失败');
    }
  } catch (error) {
    console.error('获取视频列表失败:', error);
    alert('获取视频列表失败: ' + (error.message || '未知错误'));
  } finally {
    loading.value = false;
  }
};

// 筛选视频
const filterVideos = () => {
  if (!searchQuery.value) {
    filteredVideos.value = [...videos.value];
    // 重置选择状态
    if (selectAll.value) {
      selectAll.value = false;
    }
    return;
  }
  
  const query = searchQuery.value.toLowerCase();
  filteredVideos.value = videos.value.filter(video => 
    video.title.toLowerCase().includes(query) || 
    (video.description && video.description.toLowerCase().includes(query))
  );
  
  // 更新全选状态，仅在筛选结果中的视频全部被选中时为true
  selectAll.value = filteredVideos.value.length > 0 && 
                    filteredVideos.value.every(video => selectedVideos.value.includes(video.id));
};

// 格式化时间长度
const formatDuration = (seconds) => {
  if (!seconds) return '00:00';
  
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  
  if (hours > 0) {
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  } else {
    return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }
};

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '';
  
  const date = new Date(dateString);
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  });
};

// 格式化日期时间
const formatDateTime = (dateString) => {
  if (!dateString) return '';
  
  const date = new Date(dateString);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
};

// 跳转到上传页面
const navigateToUpload = () => {
  router.push({
    name: 'VideosUpload',
    query: { courseId: courseId.value }
  });
};

// 生成知识图谱
const generateKnowledgeGraph = async (forceRegenerate = false) => {
  // 处理可能传入的事件对象
  if (typeof forceRegenerate === 'object' && forceRegenerate !== null) {
    forceRegenerate = false; // 如果传入的是事件对象，则默认为 false
  }
  
  if (!courseId.value) {
    alert('课程ID无效');
    return;
  }
  
  try {
    knowledgeGraphLoading.value = true;
    
    const response = await knowledgeMapService.generateKnowledgeGraph({
      courseId: courseId.value,
      forceRegenerate: forceRegenerate,
      incremental: true // 默认使用增量模式
    });
    
    if (response.data.code === 200) {
      alert('知识图谱生成任务已启动，请稍后查看结果');
    } else {
      throw new Error(response.data.msg || '生成失败');
    }
  } catch (error) {
    console.error('生成知识图谱失败:', error);
    
    // 检查是否是409冲突状态码（已有任务在进行中）
    if (error.response && error.response.status === 409) {
      // 保存任务信息并显示强制重新生成对话框
      pendingKnowledgeGraphTask.value = error.response.data.data;
      showForceRegenerateDialog.value = true;
    } else {
      alert('生成知识图谱失败: ' + (error.message || '未知错误'));
    }
  } finally {
    knowledgeGraphLoading.value = false;
  }
};

// 强制重新生成知识图谱
const forceRegenerateKnowledgeGraph = async () => {
  showForceRegenerateDialog.value = false;
  await generateKnowledgeGraph(true);
};

// 关闭强制重新生成对话框
const closeForceRegenerateDialog = () => {
  showForceRegenerateDialog.value = false;
  pendingKnowledgeGraphTask.value = null;
};

// 查看视频详情
const showVideoDetails = (video) => {
  router.push(`/video/${video.id}`);
};

// 打开重命名对话框
const showRenameDialog = (video) => {
  Object.assign(videoEdit, {
    id: video.id,
    title: video.title,
    description: video.description || ''
  });
  showRenameModal.value = true;
};

// 关闭重命名对话框
const closeRenameDialog = () => {
  showRenameModal.value = false;
};

// 保存视频信息
const saveVideoInfo = async () => {
  if (!videoEdit.title) {
    alert('视频标题不能为空');
    return;
  }
  
  try {
    const response = await videoService.updateVideo(videoEdit.id, {
      title: videoEdit.title,
      description: videoEdit.description
    });
    
    if (response.data && response.data.code === 200) {
      // 更新本地数据
      const index = videos.value.findIndex(v => v.id === videoEdit.id);
      if (index !== -1) {
        videos.value[index] = {
          ...videos.value[index],
          title: videoEdit.title,
          description: videoEdit.description
        };
      }
      
      // 更新筛选结果
      filterVideos();
      
      // 关闭对话框
      closeRenameDialog();
      
      alert('视频信息更新成功');
    } else {
      throw new Error(response.data.message || '更新视频信息失败');
    }
  } catch (error) {
    console.error('更新视频信息失败:', error);
    alert('更新视频信息失败: ' + (error.message || '未知错误'));
  }
};

// 确认删除视频
const confirmDeleteVideo = (video) => {
  videoToDelete.value = video;
  showDeleteModal.value = true;
};

// 关闭删除对话框
const closeDeleteDialog = () => {
  showDeleteModal.value = false;
  videoToDelete.value = null;
};

// 删除视频
const deleteVideo = async () => {
  if (!videoToDelete.value) return;
  
  try {
    const response = await videoService.deleteVideo(videoToDelete.value.id);
    
    if (response.data && response.data.code === 200) {
      // 从列表中移除
      videos.value = videos.value.filter(v => v.id !== videoToDelete.value.id);
      
      // 更新筛选结果
      filterVideos();
      
      // 关闭对话框
      closeDeleteDialog();
      
      alert('视频已成功解除关联');
    } else {
      throw new Error(response.data.message || '解除视频关联失败');
    }
  } catch (error) {
    console.error('解除视频关联失败:', error);
    alert('解除视频关联失败: ' + (error.message || '未知错误'));
  }
};

// 处理视频
const processVideo = async (video) => {
  if (!video || !video.id) return;
  
  // 判断是否正在处理
  if (processingVideoId.value === video.id) {
    alert('视频正在处理中，请稍候...');
    return;
  }
  
  // 显示处理设置对话框
  currentProcessVideo.value = video;
  processSettingsTarget.value = 'single';
  showProcessSettingsModal.value = true;
};

// 获取步骤显示名称
const getStepDisplayName = (stepName) => {
  const stepMap = {
    keyframes: '关键帧提取',
    ocr: 'OCR文字识别',
    asr: 'ASR语音识别',
    vector: '向量化处理',
    summary: '智能摘要'
  };
  return stepMap[stepName] || stepName;
};

// 检查视频处理状态
const checkVideoProcessingStatus = async () => {
  if (!currentProcessVideo.value) return;
  
  checkingStatus.value = true;
  try {
    const response = await videoService.getVideoProcessingStatus(currentProcessVideo.value.id);
    if (response.data && response.data.code === 200) {
      videoProcessingStatus.value = response.data.data;
    } else {
      throw new Error(response.data.message || '获取处理状态失败');
    }
  } catch (error) {
    console.error('获取视频处理状态失败:', error);
    alert('获取视频处理状态失败: ' + (error.message || '未知错误'));
  } finally {
    checkingStatus.value = false;
  }
};

// 关闭处理设置对话框
const closeProcessSettingsDialog = () => {
  showProcessSettingsModal.value = false;
  currentProcessVideo.value = null;
  videoProcessingStatus.value = null;
  processPreviewMode.value = false;
  processSelectedSteps.value = ['keyframes', 'ocr', 'asr', 'vector', 'summary'];
};

// 开始处理（根据设置）
const startProcessingWithSettings = async () => {
  if (processSettingsTarget.value === 'single') {
    await processSingleVideoWithSettings();
  } else {
    await processBatchVideosWithSettings();
  }
  closeProcessSettingsDialog();
};

// 单个视频处理（带设置）
const processSingleVideoWithSettings = async () => {
  if (!currentProcessVideo.value) return;
  
  const video = currentProcessVideo.value;
  processingVideoId.value = video.id;
  
  try {
    const requestData = {
      processing_steps: processPreviewMode.value ? null : (processSelectedSteps.value.length > 0 ? processSelectedSteps.value : null),
      preview_mode: processPreviewMode.value
    };
    
    const response = await videoService.processVideoWithSettings(video.id, requestData);
    
    if (response.data && response.data.code === 200) {
      const message = processPreviewMode.value 
        ? '视频预览处理任务已成功创建，将生成处理日志但不保存到数据库。'
        : '视频处理任务已成功创建，系统将在后台进行视频分析处理，完成后可用于智能问答。';
      alert(message);
      
      // 更新本地数据
      const index = videos.value.findIndex(v => v.id === video.id);
      if (index !== -1) {
        videos.value[index] = {
          ...videos.value[index],
          processed: !processPreviewMode.value // 预览模式不算真正处理完成
        };
      }
      
      // 更新筛选结果
      filterVideos();
    } else {
      throw new Error(response.data.message || '创建视频处理任务失败');
    }
  } catch (error) {
    console.error('处理视频失败:', error);
    alert('处理视频失败: ' + (error.message || '未知错误'));
  } finally {
    processingVideoId.value = null;
  }
};

// 批量处理视频（带设置）
const processBatchVideosWithSettings = async () => {
  if (selectedVideos.value.length === 0) {
    alert('请先选择要处理的视频');
    return;
  }
  
  // 显示进度对话框
  showBatchProgressModal.value = true;
  batchProcessing.value = true;
  batchProgress.value = 0;
  processedCount.value = 0;
  
  const processingType = processPreviewMode.value ? '预览处理' : '处理';
  processingStatus.value = [
    {
      icon: 'mdi-information-outline',
      color: 'info',
      textClass: 'text-info',
      message: `正在启动批量${processingType}任务...`
    }
  ];
  
  const totalVideos = selectedVideos.value.length;
  const videoQueue = [...selectedVideos.value];
  const videoStatus = new Map();
  
  // 更新处理状态显示
  const updateProcessingStatus = () => {
    const statusList = [];
    
    // 添加当前处理中的任务
    if (videoStatus.has('current')) {
      statusList.push({
        icon: 'mdi-cog',
        color: 'info',
        textClass: 'text-info',
        message: videoStatus.get('current').message
      });
    }
    
    // 添加成功完成的任务（最多显示5个）
    let successCount = 0;
    videoStatus.forEach((status, videoId) => {
      if (videoId !== 'current' && status.status === 'success' && successCount < 5) {
        statusList.push({
          icon: 'mdi-check',
          color: 'success',
          textClass: 'text-success',
          message: status.message
        });
        successCount++;
      }
    });
    
    // 添加失败的任务（全部显示）
    videoStatus.forEach((status, videoId) => {
      if (videoId !== 'current' && status.status === 'error') {
        statusList.push({
          icon: 'mdi-alert',
          color: 'error',
          textClass: 'text-error',
          message: status.message
        });
      }
    });
    
    // 添加排队中的任务数量
    if (videoQueue.length > 0) {
      statusList.push({
        icon: 'mdi-timer-sand',
        color: 'grey',
        textClass: 'text-medium-emphasis',
        message: `${videoQueue.length} 个视频等待${processingType}...`
      });
    }
    
    processingStatus.value = statusList;
  };
  
  // 按顺序处理所有视频
  for (let i = 0; i < videoQueue.length; i++) {
    const videoId = videoQueue[i];
    const videoTitle = videos.value.find(v => v.id === videoId)?.title || `视频 ${videoId}`;
    
    // 更新当前处理状态
    videoStatus.set('current', {
      status: 'processing',
      message: `${processingType}中：${videoTitle} (${i + 1}/${totalVideos})`
    });
    
    updateProcessingStatus();
    
    try {
      const requestData = {
        processing_steps: processPreviewMode.value ? null : (processSelectedSteps.value.length > 0 ? processSelectedSteps.value : null),
        preview_mode: processPreviewMode.value
      };
      
      const response = await videoService.processVideoWithSettings(videoId, requestData);
      
      if (response.data && response.data.code === 200) {
        // 处理成功
        videoStatus.set(videoId, {
          status: 'success',
          message: `${processingType}成功：${videoTitle}`
        });
        
        // 更新进度
        processedCount.value++;
        batchProgress.value = (processedCount.value / totalVideos) * 100;
      } else {
        // 处理失败
        videoStatus.set(videoId, {
          status: 'error',
          message: `${processingType}失败：${videoTitle} - ${response.data.message || '未知错误'}`
        });
      }
    } catch (error) {
      console.error(`${processingType}视频失败:`, error);
      videoStatus.set(videoId, {
        status: 'error',
        message: `${processingType}失败：${videoTitle} - ${error.message || '未知错误'}`
      });
    }
    
    // 更新状态显示
    updateProcessingStatus();
  }
  
  // 处理完成
  batchProcessing.value = false;
  videoStatus.delete('current');
  processingStatus.value.unshift({
    icon: 'mdi-check-circle',
    color: 'success',
    textClass: 'text-success',
    message: `批量${processingType}完成，共${processingType} ${processedCount.value} 个视频`
  });
  
  updateProcessingStatus();
};



// 初始化
onMounted(() => {
  fetchVideos();
});
</script>

<style scoped>
.content-card {
  min-height: 600px;
  display: flex;
  flex-direction: column;
}

.scrollable-content {
  overflow-y: auto;
  max-height: calc(100vh - 200px);
  flex-grow: 1;
}

.video-card {
  transition: transform 0.2s;
}

.video-card:hover {
  transform: scale(1.02);
}

.video-card.selected {
  border: 2px solid rgb(var(--v-theme-primary));
  box-shadow: 0 4px 12px rgba(var(--v-theme-primary), 0.2);
}

.video-thumbnail {
  position: relative;
}

.video-duration {
  position: absolute;
  bottom: 8px;
  right: 8px;
  background-color: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.875rem;
}

.search-field {
  max-width: 400px;
}

.text-truncate-2 {
  display: -webkit-box;
  display: box;
  -webkit-box-orient: vertical;
  box-orient: vertical;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  overflow: hidden;
}

.pa-4 {
  padding: 16px !important;
}

.video-checkbox {
  position: absolute;
  top: 8px;
  left: 8px;
  z-index: 2;
  background-color: rgba(255, 255, 255, 0.8);
  border-radius: 50%;
}

.video-thumbnail img:hover {
  cursor: pointer;
}
</style>