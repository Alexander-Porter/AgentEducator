<template>  <div class="ai-chat-container">
    <div class="chat-messages-container" ref="chatHistory">
      <!-- 消息列表 -->
      <template v-if="currentChat.messages.length > 0">
        <div v-for="(message, index) in currentChat.messages" :key="index" 
             class="mb-3 message-wrapper">
          
          <!-- 用户消息 -->
          <div v-if="message.role === 'user'" class="user-message-container">
            <div class="d-flex align-center justify-end mb-1">
              <v-avatar color="grey-lighten-1" size="24" class="ms-2">
                <v-icon color="white" size="14">mdi-account</v-icon>
              </v-avatar>
            </div>
            <div class="user-message-bubble">
              <div class="text-body-2">{{ message.content }}</div>
            </div>
          </div>
          
          <!-- AI消息 -->
          <div v-else class="ai-message-container">
            <div class="d-flex align-center mb-1">
              <v-avatar color="primary" size="24" class="me-2">
                <v-icon color="white" size="14">mdi-robot</v-icon>
              </v-avatar>
              <div class="text-caption text-medium-emphasis">AI助手</div>
            </div>
              <!-- AI消息气泡 -->
            <div class="ai-message-bubble">
              <!-- 等待状态和处理过程 -->
              <div v-if="!message.content && index === currentChat.messages.length - 1 && isTyping" 
                   class="typing-container">
                <!-- 显示当前处理状态 -->
                <div v-if="currentStatus" class="ai-thinking-status">
                  <div class="d-flex align-center mb-2">
                    <v-progress-circular 
                      indeterminate 
                      size="16" 
                      width="2" 
                      color="primary"
                      class="me-2"
                    />
                    <span class="status-text">{{ currentStatus }}</span>
                  </div>
                  
                  <!-- 状态统计信息 -->
                  <div v-if="statusStats" class="status-stats-inline">
                    <v-chip 
                      v-if="statusStats.document_count" 
                      size="x-small" 
                      color="blue-grey" 
                      variant="outlined"
                      class="me-1 mb-1"
                    >
                      <v-icon start size="x-small">mdi-file-document</v-icon>
                      {{ statusStats.document_count }} 文档
                    </v-chip>
                    <v-chip 
                      v-if="statusStats.tokens" 
                      size="x-small" 
                      color="green" 
                      variant="outlined"
                      class="me-1 mb-1"
                    >
                      <v-icon start size="x-small">mdi-counter</v-icon>
                      {{ statusStats.tokens }} Token
                    </v-chip>
                    <v-chip 
                      v-if="statusStats.sources" 
                      size="x-small" 
                      color="orange" 
                      variant="outlined"
                      class="me-1 mb-1"
                    >
                      <v-icon start size="x-small">mdi-link</v-icon>
                      {{ statusStats.sources }} 引用
                    </v-chip>
                  </div>
                </div>
                
                <!-- 默认思考状态 -->
                <div v-else class="default-thinking">
                  <div class="typing-indicator">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                  </div>
                  <span class="typing-text">AI正在思考...</span>
                </div>
              </div>
              
              <!-- 消息内容 -->
              <div v-else class="text-body-2 markdown-body" 
                   v-html="processMessageContent(message.content)" 
                   @click="handleCitationClick">
              </div>
            </div>
            
            <!-- 引用来源 -->
            <div v-if="message.sources && message.sources.length > 0" class="sources-container">
              <v-btn
                size="x-small"
                variant="text"
                density="compact"
                color="primary"
                prepend-icon="mdi-format-quote-open"
                @click="toggleSourcesVisibility(message)"
                class="sources-toggle mb-1"
              >
                引用来源 ({{ message.sources.length }})
                <v-icon end size="small">{{ message.showSources ? 'mdi-chevron-up' : 'mdi-chevron-down' }}</v-icon>
              </v-btn>
              
              <v-expand-transition>
                <div v-if="message.showSources" class="sources-list">
                  <v-card v-for="source in message.sources" :key="source.index" 
                          class="mb-2 source-card" variant="outlined" density="compact">
                    <v-card-item class="pa-2">
                      <v-card-title class="text-caption pb-1">
                        <v-chip size="x-small" color="primary" class="font-weight-medium me-1">{{ source.index }}</v-chip>
                        {{ source.video_title || '未知视频' }}
                      </v-card-title>
                      <v-card-subtitle class="pt-0 pb-1">
                        <v-icon size="x-small" color="primary" class="me-1">mdi-clock-outline</v-icon>
                        {{ source.time_formatted }}
                      </v-card-subtitle>
                    </v-card-item>
                    <v-card-text class="pt-0 pb-1 px-2">
                      <div class="text-caption source-content">{{ source.content }}</div>
                    </v-card-text>
                    <v-card-actions class="pa-2">
                      <v-spacer></v-spacer>
                      <v-btn 
                        variant="text" 
                        color="primary"
                        size="x-small"
                        prepend-icon="mdi-play"
                        @click="jumpToVideoTimepoint(source.video_id, source.time_point)"
                      >
                        跳转到此处
                      </v-btn>
                    </v-card-actions>
                  </v-card>
                </div>
              </v-expand-transition>
            </div>
          </div>
        </div>
      </template>
      
      <!-- 空状态 -->
      <div v-else class="empty-state">
        <div class="d-flex flex-column align-center justify-center h-100">
          <v-icon color="primary" size="48" class="mb-3">mdi-robot-outline</v-icon>
          <h3 class="text-subtitle-1 text-center mb-2">AI助手</h3>
          <p class="text-caption text-medium-emphasis text-center">
            {{ getCurrentModeDescription() }}
          </p>
        </div>
      </div>
    </div>
    
    <div class="chat-input-container">
      <v-divider></v-divider>
      
      <!-- 合并的操作和模式选择区域 -->
      <div class="chat-controls-row">
        <div class="d-flex align-center justify-space-between w-100">
          <!-- 左侧：操作按钮 -->
          <div class="d-flex align-center">
            <v-btn 
              prepend-icon="mdi-plus" 
              color="success" 
              @click="createNewChat" 
              size="x-small" 
              class="me-2"
            >
              新对话
            </v-btn>
            <v-btn 
              prepend-icon="mdi-history" 
              color="primary" 
              variant="outlined"
              @click="showHistoryDrawer = true" 
              size="x-small"
            >
              历史对话
            </v-btn>
          </div>
          
          <!-- 右侧：问答模式选择 -->
          <div class="d-flex align-center">
            <v-icon size="small" class="me-2 text-grey">mdi-comment-question-outline</v-icon>
            <span class="text-caption text-grey me-2">问答模式:</span>
            <v-select
              v-model="selectedChatMode"
              :items="chatModeOptions"
              item-title="label"
              item-value="value"
              variant="outlined"
              density="compact"
              hide-details
              class="mode-selector"
              :prepend-inner-icon="getCurrentModeIcon()"
            >
              <template v-slot:selection="{ item }">
                <span class="text-caption">{{ item.title }}</span>
              </template>
              <template v-slot:item="{ item }">
                <v-list-item :prepend-icon="item.raw.icon" @click="selectedChatMode = item.raw.value">
                  <v-list-item-title>{{ item.raw.label }}</v-list-item-title>
                  <v-list-item-subtitle class="text-caption">{{ item.raw.description }}</v-list-item-subtitle>
                </v-list-item>
              </template>
            </v-select>
          </div>
        </div>
      </div>
      
      <!-- 输入区域 -->
      <div class="ai-input-row">
        <div class="ai-input-actions">
          <v-btn icon :color="isRecording ? 'primary' : 'grey'" @click="toggleVoiceInput" class="ai-input-btn-small">
            <v-icon size="small">{{ isRecording ? 'mdi-microphone' : 'mdi-microphone-outline' }}</v-icon>
          </v-btn>
        </div>
        <v-textarea
          v-model="userInput"
          placeholder="输入您的问题..."
          rows="2"
          auto-grow
          density="compact"
          hide-details
          variant="outlined"
          class="ai-input-textarea-large"
          @keydown.enter.prevent="sendMessage"
          :disabled="isTyping"
          ref="inputField"
        ></v-textarea>
        <v-btn
          color="primary"
          icon
          @click="sendMessage"
          class="ai-input-send-btn"
          :disabled="!userInput.trim() || isTyping"
          size="small"
        >
          <v-icon size="small">mdi-send</v-icon>
        </v-btn>
      </div>
    </div>
    
    <!-- 历史对话抽屉 -->
    <v-navigation-drawer
      v-model="showHistoryDrawer"
      location="left"
      temporary
      width="320"
    >
      <v-toolbar color="primary" class="text-white">
        <v-toolbar-title>历史对话</v-toolbar-title>
        <v-spacer></v-spacer>
        <v-btn icon @click="showHistoryDrawer = false">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-toolbar>
      
      <v-list>
        <v-list-item v-if="historyLoading" class="d-flex justify-center">
          <v-progress-circular indeterminate color="primary"></v-progress-circular>
        </v-list-item>
        
        <template v-else-if="chatHistoryList.length > 0">
          <v-list-item
            v-for="chat in chatHistoryList"
            :key="chat.id"
            @click="loadHistoryChat(chat)"
            :class="{ 'bg-primary-lighten-5': currentChat.id === chat.id }"
            class="mb-1"
          >
            <template v-slot:prepend>
              <v-icon :color="chat.video_id ? 'blue' : 'green'">
                {{ chat.video_id ? 'mdi-video-outline' : 'mdi-chat-outline' }}
              </v-icon>
            </template>
            
            <v-list-item-title class="text-truncate">
              {{ chat.title }}
            </v-list-item-title>
            
            <v-list-item-subtitle class="text-caption">
              {{ formatDate(chat.updated_at) }} · {{ chat.message_count }}条消息
            </v-list-item-subtitle>
            
            <template v-slot:append>
              <v-menu>
                <template v-slot:activator="{ props }">
                  <v-btn 
                    icon="mdi-dots-vertical" 
                    variant="text" 
                    size="small"
                    v-bind="props"
                  ></v-btn>
                </template>
                <v-list density="compact">
                  <v-list-item @click="editSessionTitle(chat)">
                    <template v-slot:prepend>
                      <v-icon size="small">mdi-pencil</v-icon>
                    </template>
                    <v-list-item-title>重命名</v-list-item-title>
                  </v-list-item>
                  <v-list-item @click="deleteHistoryChat(chat.id)">
                    <template v-slot:prepend>
                      <v-icon size="small" color="error">mdi-delete</v-icon>
                    </template>
                    <v-list-item-title class="text-error">删除</v-list-item-title>
                  </v-list-item>
                </v-list>
              </v-menu>
            </template>
          </v-list-item>
        </template>
        
        <v-list-item v-else>
          <v-list-item-title class="text-body-2 text-grey text-center">
            暂无历史对话
          </v-list-item-title>
        </v-list-item>
      </v-list>
    </v-navigation-drawer>
    
    <!-- 重命名对话框 -->
    <v-dialog v-model="showEditDialog" max-width="400">
      <v-card>
        <v-card-title>重命名对话</v-card-title>
        <v-card-text>
          <v-text-field
            v-model="editTitle"
            label="对话标题"
            variant="outlined"
            hide-details
            density="compact"
          ></v-text-field>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="grey" variant="text" @click="showEditDialog = false">取消</v-btn>
          <v-btn color="primary" @click="updateSessionTitle">保存</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onBeforeUnmount, nextTick, computed } from 'vue';
import qaService from '../api/qaService';
import chatHistoryService from '../api/chatHistoryService';
import type { ChatSession, ChatMessage as HistoryMessage } from '../api/chatHistoryService';
import { formatTimeFromSeconds } from '../utils/timeFormatter';
import Tesseract from 'tesseract.js';
import { format } from 'date-fns';
import apiClient from '../api/index';
import { processContent } from '../utils/markdownRenderer';

// 属性定义
const props = defineProps<{
  videoId: string
  courseId: string
  autoPrompt?: string  // 添加自动对话的提示词prop
}>()

// 事件
const emit = defineEmits(['jump-to-timepoint', 'jump-to-video-timepoint', 'update:autoPrompt'])

// 状态定义
const userInput = ref('');
const messages = ref<any[]>([]);
const isTyping = ref(false);
const chatHistory = ref<HTMLElement | null>(null);
const sessionId = ref<string | null>(null);
const inputField = ref<HTMLTextAreaElement | null>(null);
const isRecording = ref(false);
const showHistoryDrawer = ref(false);
const showEditDialog = ref(false);
const editTitle = ref('');
const editingChatId = ref<string | null>(null);
const historyLoading = ref(false);

// 状态显示相关
const currentStatus = ref<string>('');
const statusStats = ref<any>(null);
const showStatus = ref(false);
const chatHistoryList = ref<ChatSession[]>([]);
let recognition: any = null;
const selectedChatMode = ref('video');

// 处理状态事件
const handleStatusEvent = (statusData: any) => {
  currentStatus.value = statusData.message || '';
  
  // 如果有统计信息则更新
  if (statusData.stats) {
    statusStats.value = statusData.stats;
  }
  
  // 确保状态显示在AI思考中
  showStatus.value = true;
  
  // 根据不同阶段执行不同操作
  switch(statusData.stage) {
    case 'retrieval_start':
      // 开始检索时，显示状态
      break;
      
    case 'retrieval_complete':
      // 检索完成，显示文档数量
      break;
      
    case 'question_analysis':
      // 问题分析阶段
      break;
      
    case 'generation_start':
      // 生成开始阶段，2秒后自动隐藏状态栏外层显示
      // 但在AI思考中的状态仍然保留
      setTimeout(() => {
        showStatus.value = false;
      }, 2000);
      break;
      
    case 'analysis_start':
      // 通用模式分析开始
      break;
  }
};

// 对话模式选项
const chatModeOptions = computed(() => {
  const options = [];
  
  if (props.videoId) {
    options.push({
      value: 'video',
      label: '当前视频',
      icon: 'mdi-video',
      description: '基于当前视频内容进行问答'
    });
  }
  
  if (props.courseId) {
    options.push({
      value: 'course',
      label: '整个课程',
      icon: 'mdi-book',
      description: '基于整个课程所有视频进行问答'
    });
  }
  
  options.push({
    value: 'all',
    label: '全平台',
    icon: 'mdi-earth',
    description: '基于您可访问的所有课程进行问答'
  });
  
  options.push({
    value: 'general',
    label: '通用AI',
    icon: 'mdi-robot',
    description: '通用大语言模型对话'
  });
  
  return options;
});

// 获取当前模式图标
const getCurrentModeIcon = () => {
  const currentMode = chatModeOptions.value.find(option => option.value === selectedChatMode.value);
  return currentMode ? currentMode.icon : 'mdi-comment-question-outline';
};

// 获取当前模式描述
const getCurrentModeDescription = () => {
  const currentMode = chatModeOptions.value.find(option => option.value === selectedChatMode.value);
  return currentMode ? currentMode.description : '未知模式';
};

// 处理引用标记点击事件
const handleCitationClick = (event: MouseEvent) => {
  const target = event.target as HTMLElement;
  
  // 检查是否点击的是引用标记
  if (target && target.classList.contains('citation-ref')) {
    event.preventDefault();
    event.stopPropagation();
    
    // 获取引用编号
    const index = parseInt(target.getAttribute('data-index') || '0', 10);
    if (index === 0) return;
    
    // 查找对应的消息和源
    const message = currentChat.value.messages.find(msg => 
      msg.role === 'assistant' && msg.sources && msg.sources.some((s: Source) => s.index === index));
    
    if (message) {
      const source = message.sources?.find((s: Source) => s.index === index);
      if (source && source.time_point !== undefined) {
        jumpToVideoTimepoint(source.video_id, source.time_point);
      }
    }
  }
}

// 处理消息渲染，支持Markdown并将引用标记转换为可点击的元素
const processMessageContent = (content: string): string => {
  if (!content) return '';
  
  // 使用工具函数处理Markdown和引用标记
  return processContent(content);
}

// 切换引用来源的显示状态
const toggleSourcesVisibility = (message: ChatMessage) => {
  message.showSources = !message.showSources;
}

interface Source {
  index: number
  video_id: string
  video_title: string
  time_point: number
  time_formatted: string
  content: string
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: Source[];
  error?: boolean;
  showSources?: boolean; // 控制源文档列表显示状态
}

interface Chat {
  id: string | null;
  title: string;
  time: string;
  messages: ChatMessage[];
}

const currentChat = ref<Chat>({
  id: null,
  title: '新对话',
  time: new Date().toLocaleString(),
  messages: []
});

// 加载聊天历史列表
const loadChatHistory = async () => {
  historyLoading.value = true;
  try {
    const response = await chatHistoryService.getChatSessionsList({
      videoId: props.videoId,
      courseId: props.courseId
    });
    
    if (response.data.code === 200) {
      chatHistoryList.value = response.data.data.list;
    } else {
      console.error('加载聊天历史失败:', response.data.message);
    }
  } catch (error) {
    console.error('加载聊天历史出错:', error);
  } finally {
    historyLoading.value = false;
  }
};

// 加载聊天历史详情
const loadHistoryChat = async (chat: ChatSession) => {
  historyLoading.value = true;
  try {
    const response = await chatHistoryService.getChatSessionDetail(chat.id);
    
    if (response.data.code === 200) {
      const data = response.data.data;
      
      // 构造符合当前组件格式的消息
      const formattedMessages = data.messages.map((msg: HistoryMessage) => ({
        role: msg.role,
        content: msg.content,
        timestamp: new Date(msg.created_at),
        sources: msg.time_references || []
      }));
      
      // 更新当前会话
      currentChat.value = {
        id: data.session.id,
        title: data.session.title,
        time: data.session.updated_at,
        messages: formattedMessages
      };
      
      // 获取会话ID
      sessionId.value = data.session.id;
      
      // 关闭抽屉
      showHistoryDrawer.value = false;
      
      // 滚动到底部
      scrollToBottom();
    } else {
      console.error('加载聊天详情失败:', response.data.message);
    }
  } catch (error) {
    console.error('加载聊天详情出错:', error);
  } finally {
    historyLoading.value = false;
  }
};

// 创建新的聊天会话
const createNewChat = async () => {
  // 重置当前会话
  currentChat.value = {
    id: null,
    title: '新对话',
    time: new Date().toLocaleString(),
    messages: []
  };
  
  // 重置会话ID
  sessionId.value = null;
  
  // 清空输入框
  userInput.value = '';
  
  // 聚焦输入框
  if (inputField.value) {
    inputField.value.focus();
  }
};

// 删除聊天历史
const deleteHistoryChat = async (id: string) => {
  if (!id) return;
  
  try {
    const response = await chatHistoryService.deleteChatSession(id);
    
    if (response.data.code === 200) {
      // 从列表中移除
      chatHistoryList.value = chatHistoryList.value.filter(chat => chat.id !== id);
      
      // 如果删除的是当前会话，创建新会话
      if (currentChat.value.id === id) {
        createNewChat();
      }
    } else {
      console.error('删除聊天历史失败:', response.data.message);
    }
  } catch (error) {
    console.error('删除聊天历史出错:', error);
  }
};

// 编辑会话标题
const editSessionTitle = (chat: ChatSession) => {
  editingChatId.value = chat.id;
  editTitle.value = chat.title;
  showEditDialog.value = true;
};

// 更新会话标题
const updateSessionTitle = async () => {
  if (!editingChatId.value || !editTitle.value.trim()) {
    showEditDialog.value = false;
    return;
  }
  
  try {
    const response = await chatHistoryService.updateChatSession(
      editingChatId.value,
      { title: editTitle.value.trim() }
    );
    
    if (response.data.code === 200) {
      // 更新列表中的标题
      const chatIndex = chatHistoryList.value.findIndex(c => c.id === editingChatId.value);
      if (chatIndex >= 0) {
        chatHistoryList.value[chatIndex].title = editTitle.value.trim();
      }
      
      // 如果是当前会话，也更新当前会话标题
      if (currentChat.value.id === editingChatId.value) {
        currentChat.value.title = editTitle.value.trim();
      }
    } else {
      console.error('更新标题失败:', response.data.message);
    }
  } catch (error) {
    console.error('更新标题出错:', error);
  } finally {
    showEditDialog.value = false;
    editingChatId.value = null;
  }
};

// 格式化日期
const formatDate = (dateStr: string) => {
  try {
    return format(new Date(dateStr), 'yyyy-MM-dd HH:mm');
  } catch (e) {
    return dateStr;
  }
};

// 发送消息处理
const sendMessage = async () => {
  const userMessage = userInput.value.trim();
  if (!userMessage) {
    return;
  }
  
  // 创建用户消息
  const messageContent = userMessage;
  
  // 添加用户消息到当前对话
  currentChat.value.messages.push({
    role: 'user',
    content: messageContent,
    timestamp: new Date()
  });
  
  // 清空输入框
  userInput.value = '';
  
  // 如果是新会话，创建会话记录
  if (!currentChat.value.id) {
    try {
      // 创建会话标题
      let title = userMessage;
      if (title.length > 30) {
        title = title.substring(0, 30) + '...';
      }
      const response = await chatHistoryService.createChatSession({
        title,
        videoId: props.videoId,
        courseId: props.courseId
      });
      if (response.data.code === 200) {
        const newSession = response.data.data;
        currentChat.value.id = newSession.id;
        currentChat.value.title = newSession.title;
        sessionId.value = newSession.id;
        loadChatHistory();
      }
    } catch (error) {
      console.error('创建会话失败:', error);
    }
  }    isTyping.value = true;
  
  // 重置并准备状态显示
  showStatus.value = false; 
  currentStatus.value = '准备处理请求...';
  statusStats.value = null;
  
  const aiMessageIndex = currentChat.value.messages.length;
  currentChat.value.messages.push({
    role: 'assistant',
    content: '',
    timestamp: new Date()
  });
  scrollToBottom();
  
  try {
    // 组装历史消息（不含最后一条AI消息）
    const history = currentChat.value.messages
      .filter((msg, idx) => idx < aiMessageIndex)
      .map(msg => ({ role: msg.role, content: msg.content }));
    
    // 根据选择的对话模式设置参数
    let requestParams: any = {
      query: messageContent.replace(/<[^>]+>/g, ''),
      sessionId: sessionId.value,
      isNewSession: !sessionId.value,
      history,
      videoId: null,
      courseId: null,
      askCourse: false,
      askAllCourse: false
    };
    
    switch (selectedChatMode.value) {
      case 'video':
        // 视频模式
        requestParams = {
          ...requestParams,
          videoId: props.videoId,
          courseId: props.courseId,
          askCourse: false,
          askAllCourse: false
        };
        break;
      case 'course':
        // 课程模式
        requestParams = {
          ...requestParams,
          videoId: props.videoId,
          courseId: props.courseId,
          askCourse: true,
          askAllCourse: false
        };
        break;
      case 'all':
        // 全平台模式
        requestParams = {
          ...requestParams,
          videoId: props.videoId,
          courseId: props.courseId,
          askCourse: false,
          askAllCourse: true
        };
        break;
      case 'general':
        // 通用AI模式
        requestParams = {
          ...requestParams,
          videoId: null,
          courseId: null,
          askCourse: false,
          askAllCourse: false
        };
        break;
    }
    
    // 请求流式API（POST）
    const response = await qaService.askQuestionStream(requestParams);
    const reader = response.body?.getReader();    let aiContent = '';
    let decoder = new TextDecoder('utf-8');
    let firstToken = true;
    let sources = [];
    let sessionObj = null;
    let buffer = ''; // 用于处理不完整的数据
    let contentBuffer = ''; // 用于缓冲内容以处理Markdown序号
    
    // 内容缓冲处理函数
    function processContentBuffer(): string {
      if (!contentBuffer) return '';
      
      // 检查是否包含潜在的Markdown序号标记
      const potentialMarkerRegex = /\d+[.）)]*\s*\*{0,2}$/;
      const completeMarkerRegex = /\d+[.）)]\s*\*{0,2}\S/;
      
      // 如果包含完整的序号标记，可以释放
      if (completeMarkerRegex.test(contentBuffer)) {
        const result = contentBuffer;
        contentBuffer = '';
        return result;
      }
      
      // 如果以句号、感叹号、问号、换行符结尾，可以释放
      if (/[.!?。！？\n]\s*$/.test(contentBuffer)) {
        const result = contentBuffer;
        contentBuffer = '';
        return result;
      }
      
      // 如果缓冲区太大，释放除了可能的序号部分
      if (contentBuffer.length > 30) {
        if (potentialMarkerRegex.test(contentBuffer)) {
          // 找到最后一个数字的位置
          let lastDigitPos = -1;
          for (let i = contentBuffer.length - 1; i >= 0; i--) {
            if (/\d/.test(contentBuffer[i])) {
              lastDigitPos = i;
              break;
            }
          }
          
          if (lastDigitPos > 5) {
            const result = contentBuffer.substring(0, lastDigitPos);
            contentBuffer = contentBuffer.substring(lastDigitPos);
            return result;
          }
        } else {
          const result = contentBuffer;
          contentBuffer = '';
          return result;
        }
      }
      
      return '';
    }
    
    while (true) {
      const { done, value } = await reader!.read();
      if (done) break;
      
      // 将新数据添加到缓冲区
      buffer += decoder.decode(value, { stream: true });
      
      // 按行分割数据
      const lines = buffer.split('\n');
      
      // 保留最后一行（可能不完整）
      buffer = lines.pop() || '';
      
      for (const line of lines) {
        if (!line.trim()) continue; // 跳过空行
          // 处理 data: 行
        if (line.startsWith('data: ')) {
          const content = line.substring(6); // 'data: '.length = 6
            // 尝试解析JSON（可能是源文档、会话信息或状态事件）
          try {
            const jsonData = JSON.parse(content);
            
            // 处理状态事件
            if (jsonData.type === 'status') {
              handleStatusEvent(jsonData);
              
              // 如果是第一个token的状态事件，不要标记为不是第一个token
              // 因为我们还没收到实际的文本内容
              continue;
            }
            
            // 处理其他JSON数据
            if (jsonData.sources) {
              sources = jsonData.sources;
            }
            if (jsonData.session) {
              sessionObj = jsonData.session;
            }
            if (jsonData.stats) {
              statusStats.value = jsonData.stats;
            }
            continue;
          } catch (e) {
            // 不是JSON，当作普通文本处理
          }
            // 处理文本内容
          let textContent = content;
          
          // 特殊处理：空的data行表示换行
          if (textContent === '') {
            textContent = '\n';
          }
          // 处理转义的换行符
          else if (textContent === '\\n') {
            textContent = '\n';
          }
          // 处理其他可能的换行表示
          else if (textContent === '\n' || textContent === '\r\n') {
            textContent = '\n';
          }
          // 处理包含换行符的内容
          else if (textContent.includes('\\n')) {
            textContent = textContent.replace(/\\n/g, '\n');
          }
          
          // 使用内容缓冲区处理Markdown序号分割问题
          contentBuffer += textContent;
          const processedContent = processContentBuffer();
          
          if (processedContent) {
            aiContent += processedContent;
            
            if (firstToken) {
              const aiMessage = {
                role: 'assistant' as const,
                content: aiContent,
                timestamp: new Date(),
                sources: []
              };
              currentChat.value.messages[aiMessageIndex] = aiMessage;
              firstToken = false;
            } else {
              currentChat.value.messages[aiMessageIndex].content = aiContent;
            }
            
            // 实时更新显示（限制频率以提高性能）
            scrollToBottom();
          }
        }
      }    }      // 处理剩余的缓冲区内容
    if (buffer.trim()) {
      if (buffer.startsWith('data: ')) {
        const content = buffer.substring(6);
        try {
          const jsonData = JSON.parse(content);
          
          // 处理状态事件
          if (jsonData.type === 'status') {
            handleStatusEvent(jsonData);
          } else {
            // 处理其他JSON数据
            if (jsonData.sources) {
              sources = jsonData.sources;
            }
            if (jsonData.session) {
              sessionObj = jsonData.session;
            }
            if (jsonData.stats) {
              statusStats.value = jsonData.stats;
            }
          }
        } catch (e) {
          // 不是JSON，当作普通文本处理
          contentBuffer += content;
          const processedContent = processContentBuffer();
          if (processedContent) {
            aiContent += processedContent;
            currentChat.value.messages[aiMessageIndex].content = aiContent;
          }
        }
      }
    }
    
    // 流结束时，处理剩余的内容缓冲区
    if (contentBuffer) {
      aiContent += contentBuffer;
      currentChat.value.messages[aiMessageIndex].content = aiContent;
      contentBuffer = '';
    }
    
    // 设置源文档
    if (sources.length > 0) {
      currentChat.value.messages[aiMessageIndex].sources = sources;
      currentChat.value.messages[aiMessageIndex].showSources = false;
    }
    
    // 解析sessionId
    if (sessionObj && sessionObj.sessionId) {
      sessionId.value = sessionObj.sessionId;
      currentChat.value.id = sessionObj.sessionId;    }
      } catch (error) {
    console.error('AI回复错误:', error);
    const errorMessage = {
      role: 'assistant' as const,
      content: '抱歉，我遇到了一些问题，无法回答您的问题。请稍后再试。',
      timestamp: new Date(),
      error: true
    };
    currentChat.value.messages[aiMessageIndex] = errorMessage;  } finally {
    isTyping.value = false;
    showStatus.value = false; // 隐藏状态栏
    currentStatus.value = '';
    statusStats.value = null;
  }
};

// 格式化时间
const formatTime = (timestamp: Date) => {
  const now = new Date();
  const time = new Date(timestamp);
  
  // 如果是同一天，只显示时间
  if (time.toDateString() === now.toDateString()) {
    return time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }
  
  // 否则显示日期和时间
  return `${time.toLocaleDateString()} ${time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
};


// 跳转到指定时间点
const jumpToTimepoint = (seconds: number) => {
  emit('jump-to-timepoint', seconds);
};

const jumpToVideoTimepoint = (videoId: string, seconds: number) => {
  console.log('跳转到视频时间点:', videoId, seconds);
  emit('jump-to-video-timepoint', videoId, seconds);
};

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (chatHistory.value) {
      chatHistory.value.scrollTop = chatHistory.value.scrollHeight;
    }
  });
};

// 组件挂载时加载聊天历史
onMounted(() => {
  // 根据props设置默认对话模式
  if (props.videoId) {
    selectedChatMode.value = 'video';
  } else if (props.courseId) {
    selectedChatMode.value = 'course';
  } else {
    selectedChatMode.value = 'general';
  }
  
  loadChatHistory();
  
  // 初始化WebSpeech API（如果浏览器支持）
  if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    recognition = window.webkitSpeechRecognition || window.SpeechRecognition;
    recognition = new recognition();
    recognition.continuous = true;
    recognition.lang = 'zh-CN';
    
    recognition.onresult = (event: any) => {
      const transcript = event.results[event.results.length - 1][0].transcript;
      userInput.value += transcript;
    };
    
    recognition.onend = () => {
      isRecording.value = false;
    };
  }

  // 监听auto-chat事件
  document.querySelector('.ai-chat-container')?.addEventListener('auto-chat', ((event: CustomEvent) => {
    const { prompt } = event.detail
    if (prompt) {
      userInput.value = prompt
      nextTick(() => {
        sendMessage()
      })
    }
  }) as EventListener)
});

// 观察消息变化，自动滚动到底部
watch(messages, () => {
  nextTick(() => {
    scrollToBottom();
  });
});

// 组件卸载前清理会话
onBeforeUnmount(() => {
  document.querySelector('.ai-chat-container')?.removeEventListener('auto-chat', (() => {}) as EventListener)
});

const toggleVoiceInput = () => {
  if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
    alert('当前浏览器不支持语音识别');
    return;
  }
  if (!recognition) {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.lang = 'zh-CN';
    recognition.continuous = true;
    recognition.interimResults = false;
    recognition.onresult = (event: any) => {
      if (event.results && event.results.length > 0) {
        let transcript = '';
        for (let i = 0; i < event.results.length; i++) {
          transcript += event.results[i][0].transcript;
        }
        userInput.value = transcript;
      }
    };
    recognition.onerror = () => {
      isRecording.value = false;
    };
    recognition.onend = () => {
      if (isRecording.value) {
        recognition.start();
      }
    };
  }
  if (isRecording.value) {
    recognition.stop();
    isRecording.value = false;
  } else {
    recognition.start();
    isRecording.value = true;
  }
};

// 声明Window扩展类型
declare global {
  interface Window {
    webkitSpeechRecognition?: any;
    SpeechRecognition?: any;
  }
}

// 添加watch
watch(() => props.autoPrompt, (newPrompt) => {
  if (newPrompt) {
    // 设置输入框的值
    userInput.value = newPrompt
    // 自动发送消息
    nextTick(() => {
      sendMessage()
    })
    // 清空提示词，避免重复触发
    emit('update:autoPrompt', '')
  }
}, { immediate: true })
</script>

<style scoped>
.ai-chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

/* 状态栏样式 */
.status-bar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 8px 16px;
  border-radius: 8px;
  margin: 8px;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
  animation: slideDown 0.3s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.status-content {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-text {
  font-size: 14px;
  font-weight: 500;
}

.status-stats {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
  opacity: 0.9;
}

.stats-item {
  background: rgba(255, 255, 255, 0.2);
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 500;
}

.chat-messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
  padding-right: 4px;
}

/* 消息容器样式 */
.message-wrapper {
  animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 用户消息样式 */
.user-message-container {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  margin-left: 20%;
}

.user-message-bubble {
  background-color: rgb(var(--v-theme-primary));
  color: white;
  border-radius: 12px 12px 3px 12px;
  padding: 16px 20px;
  max-width: 100%;
  word-break: break-word;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
}

/* AI消息样式 */
.ai-message-container {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  margin-right: 20%;
}

.ai-message-bubble {
  background-color: #f5f5f5;
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 12px 12px 12px 3px;
  padding: 10px 16px 10px 36px;
  max-width: 100%;
  word-break: break-word;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

/* 等待状态样式 */
.typing-container {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 4px 2px;
  min-height: 32px;
}

/* AI思考中状态显示 */
.ai-thinking-status {
  display: flex;
  flex-direction: column;
  width: 100%;
}

.status-stats-inline {
  display: flex;
  flex-wrap: wrap;
  margin-top: 4px;
  gap: 4px;
}

.default-thinking {
  display: flex;
  align-items: center;
  gap: 8px;
}

.typing-indicator {
  display: flex;
  align-items: center;
  gap: 3px;
}

.typing-dot {
  width: 6px;
  height: 6px;
  background-color: #666;
  border-radius: 50%;
  animation: typing 1.4s infinite ease-in-out;
}

.typing-dot:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
    opacity: 0.4;
  }
  30% {
    transform: translateY(-6px);
    opacity: 1;
  }
}

.typing-text {
  color: #666;
  font-size: 12px;
  font-style: italic;
}

/* 引用来源样式 */
.sources-container {
  margin-top: 8px;
  margin-left: 26px;
  max-width: calc(100% - 26px);
}

.sources-toggle {
  background-color: rgba(var(--v-theme-primary), 0.05);
  border-radius: 6px;
}

.sources-list {
  max-height: 200px;
  overflow-y: auto;
}

.source-card {
  border-left: 2px solid #1976d2 !important;
}

.source-content {
  font-size: 11px;
  max-height: 80px;
  overflow-y: auto;
  background-color: rgba(0, 0, 0, 0.02);
  border-radius: 3px;
  padding: 4px;
  white-space: pre-wrap;
  word-break: break-word;
}

/* 引用标记样式 */
:deep(.citation-ref) {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 0.75em;
  vertical-align: super;
  color: #3498db;
  font-weight: 500;
  margin: 0 1px;
  transition: all 0.2s;
  text-decoration: none;
  padding: 0 2px;
  border-radius: 3px;
}

:deep(.citation-ref:hover) {
  background-color: rgba(52, 152, 219, 0.1);
  color: #2980b9;
  text-decoration: underline;
}

/* 空状态 */
.empty-state {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

/* 输入区域样式 */
.chat-input-container {
  margin-top: auto;
  background-color: white;
  border-top: 1px solid rgba(0, 0, 0, 0.12);
}

.chat-controls-row {
  padding: 8px 12px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  background-color: rgba(0, 0, 0, 0.01);
}

.ai-input-row {
  display: flex;
  align-items: flex-end;
  padding: 8px 12px;
  gap: 8px;
  background: #fff;
}

.ai-input-actions {
  display: flex;
  flex-direction: column;
  gap: 4px;
  align-items: center;
  justify-content: flex-end;
  height: 100%;
}

.ai-input-btn-small {
  width: 28px;
  height: 28px;
  min-width: 28px;
  min-height: 28px;
  border-radius: 4px;
  margin: 0;
  padding: 0;
}

.ai-input-textarea-large {
  flex: 1;
  min-height: 36px;
  font-size: 14px;
  margin: 0 6px;
}

.ai-input-send-btn {
  width: 32px;
  height: 32px;
  min-width: 32px;
  min-height: 32px;
  border-radius: 6px;
  margin-left: 0;
  margin-bottom: 1px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.mode-selector {
  min-width: 120px;
  max-width: 160px;
}

/* 消息列表滚动条样式 */
.chat-messages-container::-webkit-scrollbar {
  width: 4px;
}

.chat-messages-container::-webkit-scrollbar-track {
  background: transparent;
}

.chat-messages-container::-webkit-scrollbar-thumb {
  background-color: rgba(0, 0, 0, 0.15);
  border-radius: 2px;
}

.chat-messages-container::-webkit-scrollbar-thumb:hover {
  background-color: rgba(0, 0, 0, 0.25);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .chat-controls-row {
    padding: 6px 8px;
  }
  
  .chat-controls-row .d-flex:first-child {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .mode-selector {
    min-width: 100px;
    max-width: 140px;
  }
  
  .ai-input-row {
    padding: 6px 8px;
  }
}

@media (max-width: 480px) {
  .chat-controls-row .d-flex:first-child {
    flex-direction: column;
    align-items: stretch;
  }
  
  .chat-controls-row .d-flex:first-child > div {
    justify-content: center;
    margin-bottom: 4px;
  }
  
  .mode-selector {
    min-width: 80px;
    max-width: 120px;
  }
}
</style>