<template>
  <div class="ai-assistant">
    <v-container fluid class="pa-4">
      <v-card class="content-card">
        <v-card-title class="d-flex align-center py-4 px-6">
          AI助手
          <v-spacer></v-spacer>
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text class="pa-0">
          <v-row class="ma-0 fill-height">            <!-- 左侧对话历史 -->
            <v-col cols="3" class="pa-0 chat-history">
              <div class="history-section">
                <div class="d-flex align-center px-4 py-3">
                  <div class="text-subtitle-1 font-weight-medium">历史对话</div>
                  <v-spacer></v-spacer>
                  <v-btn
                    color="primary"
                    small
                    @click="startNewChat"
                    class="new-chat-btn"
                  >
                    <v-icon left>mdi-plus</v-icon>
                    新对话
                  </v-btn>
                </div>
                  <!-- 当前问答模式显示 -->
                <div v-if="qaMode !== 'general'" class="qa-mode-display px-4 pb-3">
                  <v-card variant="outlined" class="pa-3">
                    <div class="text-subtitle-2 mb-2 d-flex align-center">
                      <v-icon 
                        :color="getModeColor(qaMode)" 
                        size="small" 
                        class="mr-2"
                      >
                        {{ getModeIcon(qaMode) }}
                      </v-icon>
                      {{ getModeLabel(qaMode) }}
                    </div>
                    <div class="text-caption text-grey">
                      {{ getModeDescription(qaMode) }}
                    </div>
                  </v-card>
                </div>
                
                <!-- 当前选择的课程/视频信息 -->
                <div v-if="selectedReferences.length > 0" class="current-selection px-4 pb-3">                  <v-card variant="outlined" class="pa-3">
                    <div class="text-subtitle-2 mb-2 d-flex align-items-center justify-space-between">
                      已选择内容 ({{ selectedReferences.length }})
                      <v-btn 
                        size="x-small" 
                        variant="text" 
                        @click="clearAllReferences"
                        class="text-caption"
                      >
                        清除全部
                      </v-btn>
                    </div>
                    <div class="selected-references">
                      <div 
                        v-for="ref in selectedReferences" 
                        :key="`${ref.type}-${ref.id}`"
                        class="selected-ref-item"
                      >
                        <v-icon 
                          size="small" 
                          :color="ref.type === 'course' ? 'primary' : 'secondary'" 
                          class="mr-2"
                        >
                          {{ ref.type === 'course' ? 'mdi-book-open-variant' : 'mdi-play-circle' }}
                        </v-icon>
                        <div class="flex-grow-1">
                          <div class="text-caption font-weight-bold">{{ ref.name }}</div>
                          <div v-if="ref.courseName" class="text-caption text-grey">{{ ref.courseName }}</div>
                        </div>
                        <v-btn 
                          size="x-small" 
                          variant="text" 
                          icon
                          @click="removeReference(ref)"
                        >
                          <v-icon size="16">mdi-close</v-icon>
                        </v-btn>
                      </div>
                    </div>
                  </v-card>
                </div>
                
                <v-list nav dense class="history-list">
                  <!-- 通用对话分组 -->
                  <div v-if="generalChats.length > 0">
                    <v-subheader class="px-4 text-primary font-weight-bold">
                      <v-icon left size="small" color="primary">mdi-robot</v-icon>
                      通用AI对话
                    </v-subheader>
                    <v-list-item
                      v-for="chat in generalChats"
                      :key="chat.id || chat.title"
                      :class="{ 'active': currentChat && currentChat.id === chat.id }"
                      @click="selectChat(chat)"
                    >
                      <v-list-item-title class="chat-title">
                        {{ chat.title }}
                      </v-list-item-title>
                      <v-list-item-subtitle class="chat-time">
                        {{ chat.time }}
                      </v-list-item-subtitle>
                      
                      <!-- 操作菜单 -->
                      <template v-slot:append>
                        <v-menu offset-y>
                          <template v-slot:activator="{ props }">
                            <v-btn
                              icon
                              size="small"
                              v-bind="props"
                              @click.stop
                              class="chat-menu-btn"
                            >
                              <v-icon size="16">mdi-dots-vertical</v-icon>
                            </v-btn>
                          </template>
                          <v-list density="compact">
                            <v-list-item @click="editChatTitle(chat)">
                              <v-list-item-title>
                                <v-icon left size="16">mdi-pencil</v-icon>
                                编辑标题
                              </v-list-item-title>
                            </v-list-item>
                            <v-list-item @click="confirmDeleteChat(chat)" class="text-error">
                              <v-list-item-title>
                                <v-icon left size="16">mdi-delete</v-icon>
                                删除对话
                              </v-list-item-title>
                            </v-list-item>
                          </v-list>
                        </v-menu>
                      </template>
                    </v-list-item>
                  </div>

                  <!-- 视频对话分组 -->
                  <div v-if="videoChats.length > 0">
                    <v-divider v-if="generalChats.length > 0" class="my-2"></v-divider>
                    <v-subheader class="px-4 text-secondary font-weight-bold">
                      <v-icon left size="small" color="secondary">mdi-play-circle</v-icon>
                      视频对话
                    </v-subheader>
                    <v-list-item
                      v-for="chat in videoChats"
                      :key="chat.id || chat.title"
                      :class="{ 'active': currentChat && currentChat.id === chat.id }"
                      @click="selectChat(chat)"
                    >
                      <template v-slot:prepend>
                        <v-icon size="small" color="secondary">mdi-play-circle</v-icon>
                      </template>
                      
                      <v-list-item-title class="chat-title">
                        {{ chat.title }}
                      </v-list-item-title>
                      <v-list-item-subtitle class="chat-time">
                        <div v-if="chat.videoInfo" class="text-caption">
                          视频: {{ chat.videoInfo.title }}
                        </div>
                        <div v-if="chat.courseInfo" class="text-caption">
                          课程: {{ chat.courseInfo.name }}
                        </div>
                        <div class="text-caption">{{ chat.time }}</div>
                      </v-list-item-subtitle>
                      
                      <!-- 操作菜单 -->
                      <template v-slot:append>
                        <v-menu offset-y>
                          <template v-slot:activator="{ props }">
                            <v-btn
                              icon
                              size="small"
                              v-bind="props"
                              @click.stop
                              class="chat-menu-btn"
                            >
                              <v-icon size="16">mdi-dots-vertical</v-icon>
                            </v-btn>
                          </template>
                          <v-list density="compact">
                            <v-list-item @click="editChatTitle(chat)">
                              <v-list-item-title>
                                <v-icon left size="16">mdi-pencil</v-icon>
                                编辑标题
                              </v-list-item-title>
                            </v-list-item>
                            <v-list-item @click="confirmDeleteChat(chat)" class="text-error">
                              <v-list-item-title>
                                <v-icon left size="16">mdi-delete</v-icon>
                                删除对话
                              </v-list-item-title>
                            </v-list-item>
                          </v-list>
                        </v-menu>
                      </template>
                    </v-list-item>
                  </div>

                  <!-- 课程对话分组 -->
                  <div v-if="courseChats.length > 0">
                    <v-divider v-if="generalChats.length > 0 || videoChats.length > 0" class="my-2"></v-divider>
                    <v-subheader class="px-4 text-warning font-weight-bold">
                      <v-icon left size="small" color="warning">mdi-book-open-variant</v-icon>
                      课程对话
                    </v-subheader>
                    <v-list-item
                      v-for="chat in courseChats"
                      :key="chat.id || chat.title"
                      :class="{ 'active': currentChat && currentChat.id === chat.id }"
                      @click="selectChat(chat)"
                    >
                      <template v-slot:prepend>
                        <v-icon size="small" color="warning">mdi-book-open-variant</v-icon>
                      </template>
                      
                      <v-list-item-title class="chat-title">
                        {{ chat.title }}
                      </v-list-item-title>
                      <v-list-item-subtitle class="chat-time">
                        <div v-if="chat.courseInfo" class="text-caption">
                          课程: {{ chat.courseInfo.name }}
                        </div>
                        <div class="text-caption">{{ chat.time }}</div>
                      </v-list-item-subtitle>
                      
                      <!-- 操作菜单 -->
                      <template v-slot:append>
                        <v-menu offset-y>
                          <template v-slot:activator="{ props }">
                            <v-btn
                              icon
                              size="small"
                              v-bind="props"
                              @click.stop
                              class="chat-menu-btn"
                            >
                              <v-icon size="16">mdi-dots-vertical</v-icon>
                            </v-btn>
                          </template>
                          <v-list density="compact">
                            <v-list-item @click="editChatTitle(chat)">
                              <v-list-item-title>
                                <v-icon left size="16">mdi-pencil</v-icon>
                                编辑标题
                              </v-list-item-title>
                            </v-list-item>
                            <v-list-item @click="confirmDeleteChat(chat)" class="text-error">
                              <v-list-item-title>
                                <v-icon left size="16">mdi-delete</v-icon>
                                删除对话
                              </v-list-item-title>
                            </v-list-item>
                          </v-list>
                        </v-menu>
                      </template>
                    </v-list-item>
                  </div>
                  
                  <!-- 如果没有任何对话 -->
                  <div v-if="chatHistory.length === 0" class="text-center py-4">
                    <v-icon size="48" color="grey">mdi-chat-outline</v-icon>
                    <div class="text-caption text-grey mt-2">暂无历史对话</div>
                  </div>
                </v-list>
              </div>
            </v-col>            <!-- 右侧聊天区域 -->
            <v-col cols="9" class="pa-0 chat-main">
              <!-- 状态显示区域 -->
              <v-slide-y-transition>
                <div v-if="showStatus" class="status-bar">
                  <div class="status-content">
                    <v-progress-circular 
                      indeterminate 
                      size="16" 
                      width="2" 
                      color="primary"
                      class="me-2"
                    />
                    <span class="status-text">{{ currentStatus }}</span>
                    <div v-if="statusStats" class="status-stats">
                      <span v-if="statusStats.document_count" class="stats-item">
                        文档片段: {{ statusStats.document_count }}
                      </span>
                      <span v-if="statusStats.tokens" class="stats-item">
                        Token: {{ statusStats.tokens }}
                      </span>
                      <span v-if="statusStats.sources" class="stats-item">
                        引用: {{ statusStats.sources }}
                      </span>
                    </div>
                  </div>
                </div>
              </v-slide-y-transition>
              
              <!-- 聊天消息区域 -->
              <div class="chat-messages" ref="messagesContainer">
                <div v-if="currentChat" v-for="(message, index) in currentChat.messages" :key="message.id" 
                     :class="['message-wrapper', message.role]">
                  <div class="message-content">
                    <!-- 只有在不是typing状态时，或者不是最后一条空内容的AI消息时，才显示头像 -->
                    <div class="message-avatar" v-if="message.role === 'assistant' && !(isTyping && index === currentChat.messages.length - 1 && !message.content.trim())">
                      <v-avatar color="primary" size="40">
                        <v-icon dark>mdi-robot</v-icon>
                      </v-avatar>
                    </div>
                    <div class="message-bubble" v-if="message.content.trim() || !isTyping || index !== currentChat.messages.length - 1">
                      <div class="message-text markdown-body" v-html="processMessageContent(message.content)" @click="handleCitationClick"></div>
                      <div class="message-time">{{ message.time }}</div>
                      <div v-if="message.sources && message.sources.length > 0" class="message-sources">
                        <div class="message-sources-toggle" @click="toggleSourcesVisibility(message)">
                          引用来源 ({{ message.sources.length }})
                          <v-icon small>{{ message.showSources ? 'mdi-chevron-up' : 'mdi-chevron-down' }}</v-icon>
                        </div>
                        <div v-if="message.showSources" class="message-sources-list">
                          <div v-for="source in message.sources" :key="source.index" class="source-item">
                            <div class="source-index">[{{ source.index }}]</div>
                            <div class="source-content">
                              <div class="source-title">{{ source.video_title || '未知视频' }}</div>
                              <div class="source-time">时间点: {{ source.time_formatted }}</div>
                              <div class="source-preview">{{ source.content }}</div>
                              <v-btn 
                                x-small 
                                color="primary" 
                                text
                                @click="navigateToVideo(source.video_id, source.time_point)"
                              >
                                <v-icon x-small left>mdi-play</v-icon>
                                跳转到视频
                              </v-btn>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                    <div class="message-avatar" v-if="message.role === 'user'">
                      <v-avatar color="grey" size="40">
                        <v-icon dark>mdi-account</v-icon>
                      </v-avatar>
                    </div>
                  </div>
                </div>
                <div v-if="isTyping && (!currentChat?.messages.length || currentChat.messages[currentChat.messages.length - 1].role === 'user')" class="message-wrapper assistant">
                  <div class="message-content">
                    <div class="message-avatar">
                      <v-avatar color="primary" size="40">
                        <v-icon dark>mdi-robot</v-icon>
                      </v-avatar>
                    </div>
                    <div class="message-bubble typing">
                      <span class="dot"></span>
                      <span class="dot"></span>
                      <span class="dot"></span>
                    </div>
                  </div>
                </div>
                <div v-if="!currentChat || currentChat.messages.length === 0" class="empty-chat">
                  <div class="empty-icon">
                    <v-icon size="64" color="grey">mdi-robot-outline</v-icon>
                  </div>
                  <div class="empty-text">开始与AI助手对话吧！</div>
                </div>
              </div>              <!-- 输入区域 -->
              <div class="ai-input-row">
                <div class="ai-input-actions">
                  <v-btn icon :color="isRecording ? 'primary' : 'grey'" @click="toggleVoiceInput" class="ai-input-btn-small">
                    <v-icon>{{ isRecording ? 'mdi-microphone' : 'mdi-microphone-outline' }}</v-icon>
                  </v-btn>
                  <v-btn icon @click="triggerImageUpload" class="ai-input-btn-small">
                    <v-icon>mdi-image</v-icon>
                  </v-btn>
                  <input type="file" ref="imageInput" accept="image/*" style="display:none" @change="handleImageUpload" />
                  <div v-if="uploadedImage" class="ai-uploaded-thumb">
                    <img :src="uploadedImage" alt="预览" class="ai-thumb-img" />
                    <v-btn icon size="x-small" class="ai-thumb-remove" @click="uploadedImage = null">
                      <v-icon size="16">mdi-close</v-icon>
                    </v-btn>
                  </div>
                </div>
                
                <!-- 输入框容器，包含 @ 引用建议 -->
                <div class="input-container">
                  <v-textarea
                    ref="textareaRef"
                    v-model="userInput"
                    placeholder="输入问题，支持 @ 引用课程或视频..."
                    rows="2"
                    auto-grow
                    density="compact"
                    hide-details
                    variant="outlined"                    class="ai-input-textarea-large"
                    @input="handleTextareaInput"
                    @keydown="handleKeyDown"
                    :disabled="isTyping"
                  ></v-textarea>
                  
                  <!-- @ 引用建议下拉框 -->
                  <div
                    v-if="showSuggestions"
                    class="suggestions-dropdown"
                    :style="{
                      position: 'fixed',
                      top: suggestionsPosition.top + 'px',
                      left: suggestionsPosition.left + 'px',
                      zIndex: 1000
                    }"
                  >
                    <v-card class="suggestions-card" elevation="8">
                      <v-card-text class="pa-0">
                        <div v-if="isSearchingVideos" class="suggestion-loading">
                          <v-progress-circular indeterminate size="16" class="mr-2"></v-progress-circular>
                          <span class="text-caption">搜索视频中...</span>
                        </div>
                        <div
                          v-for="(suggestion, index) in suggestionsList"
                          :key="`${suggestion.type}-${suggestion.id}`"
                          class="suggestion-item"
                          :class="{ 'suggestion-selected': index === selectedSuggestionIndex }"
                          @click="onSuggestionClick(suggestion)"
                          @mouseenter="selectedSuggestionIndex = index"
                        >
                          <div class="suggestion-content">
                            <div class="suggestion-header">
                              <v-icon 
                                :color="suggestion.type === 'course' ? 'primary' : 'secondary'"
                                size="small"
                                class="mr-2"
                              >
                                {{ suggestion.type === 'course' ? 'mdi-book-open-variant' : 'mdi-play-circle' }}
                              </v-icon>
                              <span class="suggestion-title">{{ suggestion.name }}</span>
                            </div>
                            <div v-if="suggestion.description" class="suggestion-description">
                              {{ truncate(suggestion.description, 50) }}
                            </div>
                            <div v-if="suggestion.courseName" class="suggestion-course">
                              来自课程: {{ suggestion.courseName }}
                            </div>
                          </div>
                        </div>
                        <div v-if="suggestionsList.length === 0 && !isSearchingVideos" class="suggestion-empty">
                          <span class="text-caption text-grey">没有找到匹配的课程或视频</span>
                        </div>
                      </v-card-text>
                      <v-divider></v-divider>
                      <v-card-actions class="pa-2">
                        <span class="text-caption text-grey">
                          使用 ↑↓ 选择，Enter 确认，Esc 取消
                        </span>
                      </v-card-actions>
                    </v-card>
                  </div>
                </div>
                
                <v-btn
                  color="primary"
                  icon
                  @click="sendMessage"
                  class="ai-input-send-btn"
                  :disabled="!userInput.trim() && !uploadedImage || isTyping"
                >
                  <v-icon>mdi-send</v-icon>
                </v-btn>
              </div>
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>
    </v-container>
    
    <!-- 编辑标题对话框 -->
    <v-dialog v-model="editDialog" max-width="400px">
      <v-card>
        <v-card-title class="text-h5">编辑对话标题</v-card-title>
        <v-card-text>
          <v-text-field
            v-model="editingTitle"
            label="对话标题"
            variant="outlined"
            dense
            :counter="50"
            :rules="[v => !!v || '标题不能为空', v => v.length <= 50 || '标题不能超过50个字符']"
          ></v-text-field>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text @click="editDialog = false">取消</v-btn>
          <v-btn color="primary" @click="saveEditTitle">保存</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 确认删除对话框 -->
    <v-dialog v-model="deleteDialog" max-width="400px">
      <v-card>
        <v-card-title class="text-h5">确认删除</v-card-title>
        <v-card-text>
          确定要删除对话"{{ deletingChat?.title }}"吗？此操作不可撤销，将同时删除对话中的所有消息。
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text @click="deleteDialog = false">取消</v-btn>
          <v-btn color="error" @click="deleteChat">删除</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 内容审核警告弹窗 -->
    <v-dialog v-model="contentWarningDialog" max-width="500px">
      <v-card>
        <v-card-title class="text-h5 d-flex align-center">
          <v-icon color="warning" left>mdi-alert</v-icon>
          内容审核警告
        </v-card-title>
        <v-card-text>
          <div class="warning-content">
            <p class="text-body-1 mb-3">{{ contentWarningMessage }}</p>
            <v-alert type="warning" variant="tonal" class="mb-0">
              <div class="text-body-2">
                为了营造良好的学习环境，请使用文明用语进行交流。我们鼓励：
                <ul class="mt-2 ml-4">
                  <li>礼貌友善的提问方式</li>
                  <li>具体清晰的问题描述</li>
                  <li>积极正面的学习态度</li>
                </ul>
              </div>
            </v-alert>
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" @click="contentWarningDialog = false">我知道了</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, onBeforeUnmount, computed } from 'vue'
import Tesseract from 'tesseract.js'
import qaService from '../api/qaService'
import chatHistoryService from '../api/chatHistoryService'
import courseService from '../api/courseService'
import videoService from '../api/videoService'
import { processContent } from '../utils/markdownRenderer'
import { checkContent, type ContentFilterResult } from '../utils/contentFilter'

const userInput = ref('')
const isTyping = ref(false)
const isRecording = ref(false)
const messagesContainer = ref<HTMLElement | null>(null)
const imageInput = ref<HTMLInputElement | null>(null)
let recognition: any = null
const uploadedImage = ref<string | null>(null)
const sessionId = ref<string | null>(null)

// 问答模式相关
const qaMode = ref('general') // 'general', 'video', 'course', 'all'
const selectedReferences = ref<any[]>([]) // 存储所有选择的课程和视频引用

// @ 引用功能相关
const showSuggestions = ref(false)
const suggestionsList = ref<any[]>([])
const selectedSuggestionIndex = ref(0)
const suggestionsPosition = ref({ top: 0, left: 0 })
const isSearchingVideos = ref(false)
const textareaRef = ref<HTMLTextAreaElement | null>(null)
const currentAtQuery = ref('')
const atStartPosition = ref(0)

// 状态显示相关
const currentStatus = ref<string>('')
const statusStats = ref<any>(null)
const showStatus = ref(false)

// 编辑和删除对话相关的响应式变量
const editDialog = ref(false)
const deleteDialog = ref(false)
const editingTitle = ref('')
const editingChat = ref<Chat | null>(null)
const deletingChat = ref<Chat | null>(null)

// 内容审核警告弹窗
const contentWarningDialog = ref(false)
const contentWarningMessage = ref('')

// 模式显示相关的辅助方法
const getModeColor = (mode: string) => {
  switch (mode) {
    case 'video': return 'secondary'
    case 'course': return 'primary'
    case 'all': return 'warning'
    default: return 'grey'
  }
}

const getModeIcon = (mode: string) => {
  switch (mode) {
    case 'video': return 'mdi-play-circle'
    case 'course': return 'mdi-book-open-variant'
    case 'all': return 'mdi-earth'
    default: return 'mdi-chat'
  }
}

const getModeLabel = (mode: string) => {
  switch (mode) {
    case 'video': return '视频问答'
    case 'course': return '课程问答'
    case 'all': return '全平台问答'
    default: return '通用问答'
  }
}

const getModeDescription = (mode: string) => {
  switch (mode) {
    case 'video': return '基于所选视频内容进行问答'
    case 'course': return '基于所选课程内容进行问答'
    case 'all': return '基于全平台所有内容进行问答'
    default: return '通用AI问答，不限制特定内容范围'
  }
}

// 处理状态事件
const handleStatusEvent = (statusData: any) => {
  currentStatus.value = statusData.message;
  statusStats.value = statusData.stats || null;
  showStatus.value = true;
  
  // 对于某些阶段，设置自动隐藏
  if (statusData.stage === 'generation_start') {
    setTimeout(() => {
      showStatus.value = false;
    }, 1000);
  }
}

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
    const message = currentChat.value?.messages.find(msg => 
      msg.role === 'assistant' && msg.sources && msg.sources.some(s => s.index === index));
    
    if (message) {
      const source = message.sources?.find(s => s.index === index);
      if (source) {
        // 跳转到视频
        if (source.video_id && source.time_point !== undefined) {
          // 这里可以调用一个方法来导航到视频播放页面，或者创建一个自定义事件
          window.open(`/video/${source.video_id}?t=${source.time_point}`, '_blank');
        }
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

interface Chat {
  id: string | null  // 修改为string或null，因为UUID是字符串，新会话可以是null
  title: string
  time: string
  messages: Message[]
  type: string
  videoInfo: any
  courseInfo: any
}

interface Source {
  index: number
  video_id: string
  video_title: string
  time_point: number
  time_formatted: string
  content: string
}

interface Message {
  id: number | string  // 允许number或string
  role: 'user' | 'assistant'
  content: string
  time: string
  sources?: Source[]
  error?: boolean
  showSources?: boolean  // 新增：控制源文档列表显示状态
}

// 切换源文档显示状态
const toggleSourcesVisibility = (message: Message) => {
  message.showSources = !message.showSources;
}

// 导航到视频指定时间点
const navigateToVideo = (videoId: string, timePoint: number) => {
  window.open(`/video/${videoId}?t=${timePoint}`, '_blank');
}

// 聊天历史数据
const chatHistory = ref<Chat[]>([])
const currentChat = ref<Chat | null>(null)

// 计算属性：按类型分组聊天历史
const generalChats = computed(() => chatHistory.value.filter(chat => chat.type === 'general'))
const videoChats = computed(() => chatHistory.value.filter(chat => chat.type === 'video'))
const courseChats = computed(() => chatHistory.value.filter(chat => chat.type === 'course'))

// 加载聊天历史
const loadChatHistory = async () => {
  try {
    const response = await chatHistoryService.getChatSessionsList({
      page: 1,
      size: 50,  // 获取最近50个会话
      includeAll: true  // 获取所有类型的对话
    })
    
    if (response.data.code === 200) {
      const sessions = response.data.data.list
      
      // 转换为前端所需的格式
      chatHistory.value = sessions.map((session: any) => ({
        id: session.id,
        title: session.title,
        time: formatTime(session.updated_at),
        messages: [],  // 消息会在选择会话时加载
        type: session.type,  // 对话类型
        videoInfo: session.video_info,  // 视频信息
        courseInfo: session.course_info  // 课程信息
      }))
      
      // 如果有历史会话且当前没有选中会话，选择第一个
      if (chatHistory.value.length > 0 && !currentChat.value) {
        await selectChat(chatHistory.value[0])
      }
    }
  } catch (error) {
    console.error('加载聊天历史失败:', error)
  }
}

// 格式化时间显示
const formatTime = (dateTime: string) => {
  const date = new Date(dateTime)
  const now = new Date()
  const diffTime = now.getTime() - date.getTime()
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24))
  const diffHours = Math.floor(diffTime / (1000 * 60 * 60))
  const diffMinutes = Math.floor(diffTime / (1000 * 60))
  
  if (diffDays > 0) {
    if (diffDays === 1) return '昨天'
    if (diffDays < 7) return `${diffDays}天前`
    return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
  } else if (diffHours > 0) {
    return `${diffHours}小时前`
  } else if (diffMinutes > 0) {
    return `${diffMinutes}分钟前`
  } else {
    return '刚刚'
  }
}

// 开始新对话
const startNewChat = () => {
  const newChat = {
    id: null,  // 新会话暂时没有ID
    title: '新对话',
    time: '刚刚',
    messages: [],
    type: 'general',
    videoInfo: null,
    courseInfo: null
  }
  currentChat.value = newChat
  sessionId.value = null  // 重置sessionId
}

// 选择对话
const selectChat = async (chat: Chat) => {
  try {
    currentChat.value = chat
    
    // 如果是新对话或者已经加载过消息，直接返回
    if (!chat.id || chat.messages.length > 0) {
      return
    }
    
    // 加载该会话的详细消息
    const response = await chatHistoryService.getChatSessionDetail(chat.id)
    if (response.data.code === 200) {
      const sessionData = response.data.data
      const messages = sessionData.messages || []
      
      // 转换消息格式
      chat.messages = messages.map((msg: any) => ({
        id: msg.id,
        role: msg.role,
        content: msg.content,
        time: formatMessageTime(msg.created_at),
        sources: msg.time_references || [],
        showSources: false
      }))
      
      // 设置sessionId以便继续对话
      sessionId.value = chat.id
      
      // 滚动到底部
      await nextTick()
      scrollToBottom()
    }
  } catch (error) {
    console.error('加载会话详情失败:', error)
  }
}

// 格式化消息时间
const formatMessageTime = (dateTime: string) => {
  const date = new Date(dateTime)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

// 发送消息
const sendMessage = async () => {
  if ((!userInput.value.trim() && !uploadedImage.value) || isTyping.value || !currentChat.value) return;

  // 内容审核检测
  const auditResult: ContentFilterResult = checkContent(userInput.value)
  if (!auditResult.isValid) {
    contentWarningMessage.value = auditResult.message
    contentWarningDialog.value = true
    return // 拦截发送
  }

  let content = '';
  if (uploadedImage.value) {
    content += `<img src='${uploadedImage.value}' style='max-width:220px;max-height:140px;border-radius:12px;margin:8px 0;display:block;' />`;
  }
  if (userInput.value.trim()) {
    content += `<div>${userInput.value.trim()}</div>`;
  }
  
  // 添加用户消息
  currentChat.value.messages.push({
    id: Date.now(),
    role: 'user',
    content,
    time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  });
  
  userInput.value = '';
  uploadedImage.value = null;  await nextTick();
  scrollToBottom();
  
  // 开始AI回复
  isTyping.value = true;
  
  // 显示初始状态
  currentStatus.value = '准备处理请求...';
  showStatus.value = true;
  
  try {
    // 初始化AI回复
    let aiContent = '';
    let aiSources: Source[] = [];
    let aiMessageIndex = currentChat.value.messages.length;
    
    // 获取流式响应    // 组装历史消息
    const history = currentChat.value.messages
      .filter(msg => msg.role === 'user' || msg.role === 'assistant')
      .map(msg => ({ role: msg.role, content: msg.content }));    // 根据问答模式设置参数
    let requestParams: any = {
      query: content.replace(/<[^>]+>/g, ''),
      sessionId: sessionId.value,
      isNewSession: !sessionId.value,
      history
    }

    // 根据问答模式和选择的引用设置不同的参数
    if (qaMode.value === 'video') {
      // 视频模式：取第一个视频的ID
      const videoRef = selectedReferences.value.find(ref => ref.type === 'video')
      if (videoRef) {
        requestParams.videoId = videoRef.id
        requestParams.courseId = null
        requestParams.askCourse = false
        requestParams.askAllCourse = false
      }
    } else if (qaMode.value === 'course') {
      // 课程模式：取第一个课程的ID，或者如果都是同一课程的视频，取课程ID
      const courseRef = selectedReferences.value.find(ref => ref.type === 'course')
      if (courseRef) {
        requestParams.videoId = null
        requestParams.courseId = courseRef.id
        requestParams.askCourse = true
        requestParams.askAllCourse = false
      } else {
        // 如果都是同一课程的视频，获取课程ID
        const videoRefs = selectedReferences.value.filter(ref => ref.type === 'video')
        if (videoRefs.length > 0 && videoRefs[0].courseId) {
          requestParams.videoId = null
          requestParams.courseId = videoRefs[0].courseId
          requestParams.askCourse = true
          requestParams.askAllCourse = false
        }
      }
    } else if (qaMode.value === 'all') {
      requestParams.videoId = null
      requestParams.courseId = null
      requestParams.askCourse = false
      requestParams.askAllCourse = true
    } else {
      // 通用模式
      requestParams.videoId = null
      requestParams.courseId = null
      requestParams.askCourse = false
      requestParams.askAllCourse = false
    }

    const response = await qaService.askQuestionStream(requestParams);
    if (!response.ok) {
      throw new Error('网络请求失败');
    }
    // 处理SSE流
    const reader = response.body?.getReader();
    if (!reader) throw new Error('无法读取响应');
    const decoder = new TextDecoder();
    let buffer = '';
    let firstToken = true;
    let sessionObj = null;
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n\n');
      buffer = lines.pop() || '';
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.substring(6);          try {
            const jsonData = JSON.parse(data);
            // 处理状态事件
            if (jsonData.type === 'status') {
              handleStatusEvent(jsonData);
              continue;
            }
            if (jsonData.sources) {
              aiSources = jsonData.sources;
              if (currentChat.value && currentChat.value.messages[aiMessageIndex]) {
                currentChat.value.messages[aiMessageIndex].sources = aiSources;
                // 立即处理引用标记与源的关联
                currentChat.value.messages[aiMessageIndex].content = 
                  processMessageContent(currentChat.value.messages[aiMessageIndex].content);
              }
            }
            if (jsonData.session) {
              sessionObj = jsonData.session;
            }
            continue;
          } catch (e) {}
          aiContent += data;
          if (firstToken) {
            if (currentChat.value) {
              currentChat.value.messages.push({
                id: Date.now(),
                role: 'assistant',
                content: aiContent,
                time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
                sources: aiSources,
                showSources: false  // 默认不显示源文档列表
              });
              aiMessageIndex = currentChat.value.messages.length - 1;
            }
            firstToken = false;
          } else {
            if (currentChat.value) {
              currentChat.value.messages[aiMessageIndex].content = aiContent;
            }
          }
          await nextTick();
          scrollToBottom();
        }
      }
    }
    // 解析sessionId
    if (sessionObj && sessionObj.sessionId) {
      sessionId.value = sessionObj.sessionId;
      
      // 如果是新会话，更新会话信息并添加到历史列表
      if (currentChat.value && !currentChat.value.id) {
        currentChat.value.id = sessionObj.sessionId;
        currentChat.value.title = `通用问答 - ${content.replace(/<[^>]+>/g, '').substring(0, 20)}...`;
        chatHistory.value.unshift({...currentChat.value});
      }
    }
  } catch (error) {
    console.error('AI回复错误:', error);
    if (currentChat.value) {
      currentChat.value.messages.push({
        id: Date.now(),
        role: 'assistant',
        content: '抱歉，我遇到了一些问题，无法回答您的问题。请稍后再试。',
        time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
        error: true
      });
    }  } finally {
    isTyping.value = false;
    showStatus.value = false; // 隐藏状态栏
    scrollToBottom();
  }
}

// 切换语音输入
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
}

// 滚动到底部
const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const triggerImageUpload = () => {
  imageInput.value?.click()
}

const handleImageUpload = async (event: Event) => {
  const files = (event.target as HTMLInputElement).files;
  if (!files || files.length === 0) return;
  const file = files[0];
  const reader = new FileReader();
  reader.onload = async (e) => {
    const imageData = e.target?.result;
    if (typeof imageData === 'string') {
      uploadedImage.value = imageData;
      // 可选：用Tesseract识别图片内容，结果只用于AI理解，不显示在消息里
      // const { data: { text } } = await Tesseract.recognize(imageData, 'chi_sim');
    }
    // 关键：重置input的value，允许重复上传同一图片
    if (imageInput.value) imageInput.value.value = '';
  };
  reader.readAsDataURL(file);
};

// 编辑对话标题
const editChatTitle = (chat: Chat) => {
  editingChat.value = chat
  editingTitle.value = chat.title
  editDialog.value = true
}

// 保存编辑的标题
const saveEditTitle = async () => {
  if (!editingChat.value || !editingTitle.value.trim()) return
  
  try {
    const response = await chatHistoryService.updateChatSession(editingChat.value.id!, {
      title: editingTitle.value.trim()
    })
    
    if (response.data.code === 200) {
      // 更新本地数据
      editingChat.value.title = editingTitle.value.trim()
      editDialog.value = false
      
      // 显示成功消息
      console.log('标题更新成功')
    } else {
      console.error('更新标题失败:', response.data.message)
    }
  } catch (error) {
    console.error('更新标题错误:', error)
  }
}

// 确认删除对话
const confirmDeleteChat = (chat: Chat) => {
  deletingChat.value = chat
  deleteDialog.value = true
}

// 删除对话
const deleteChat = async () => {
  if (!deletingChat.value) return
  
  try {
    const response = await chatHistoryService.deleteChatSession(deletingChat.value.id!)
    
    if (response.data.code === 200) {
      // 从本地列表中移除
      const index = chatHistory.value.findIndex(chat => chat.id === deletingChat.value!.id)
      if (index > -1) {
        chatHistory.value.splice(index, 1)
      }
      
      // 如果删除的是当前选中的对话，清除当前对话
      if (currentChat.value && currentChat.value.id === deletingChat.value.id) {
        currentChat.value = null
        sessionId.value = null
      }
      
      deleteDialog.value = false
      deletingChat.value = null
      
      // 显示成功消息
      console.log('对话删除成功')
    } else {
      console.error('删除对话失败:', response.data.message)
    }
  } catch (error) {    console.error('删除对话错误:', error)
  }
}

// 问答模式变化处理
// 智能问答模式切换
const updateQaMode = () => {
  if (selectedReferences.value.length === 0) {
    qaMode.value = 'general'
    return
  }

  const courses = selectedReferences.value.filter(ref => ref.type === 'course')
  const videos = selectedReferences.value.filter(ref => ref.type === 'video')
  
  if (videos.length === 1 && courses.length === 0) {
    // 单个视频 -> 视频模式
    qaMode.value = 'video'
  } else if (courses.length === 1) {
    // 单个课程 -> 课程模式
    qaMode.value = 'course'
  } else if (videos.length > 1 && courses.length === 0) {
    // 多个视频，检查是否同一课程
    const courseIds = [...new Set(videos.map(v => v.courseId).filter(id => id))]
    if (courseIds.length === 1) {
      // 同一课程的多个视频 -> 课程模式
      qaMode.value = 'course'
    } else {
      // 跨课程来源 -> 全平台模式
      qaMode.value = 'all'
    }
  } else {
    // 混合引用或跨课程来源 -> 全平台模式
    qaMode.value = 'all'
  }
}

// 清除所有引用
const clearAllReferences = () => {
  selectedReferences.value = []
  qaMode.value = 'general'
}

// 移除单个引用
const removeReference = (ref: any) => {
  const index = selectedReferences.value.findIndex(r => r.type === ref.type && r.id === ref.id)
  if (index > -1) {
    selectedReferences.value.splice(index, 1)
    updateQaMode()
  }
}

// 处理输入框输入事件
const handleTextareaInput = (event: Event) => {
  const textarea = event.target as HTMLTextAreaElement
  const value = textarea.value
  const cursorPos = textarea.selectionStart

  // 查找最近的 @ 符号位置
  const beforeCursor = value.substring(0, cursorPos)
  const lastAtIndex = beforeCursor.lastIndexOf('@')
  
  if (lastAtIndex === -1) {
    hideSuggestions()
    return
  }

  // 检查 @ 符号后面是否有空格或其他分隔符
  const afterAt = beforeCursor.substring(lastAtIndex + 1)
  if (/\s/.test(afterAt)) {
    hideSuggestions()
    return
  }

  // 提取查询词
  currentAtQuery.value = afterAt
  atStartPosition.value = lastAtIndex

  // 如果查询词长度大于0，显示建议
  if (currentAtQuery.value.length >= 0) {
    showSuggestionsDropdown(textarea)
    searchSuggestions(currentAtQuery.value)
  } else {
    hideSuggestions()
  }
}

// 处理键盘事件
const handleKeyDown = (event: KeyboardEvent) => {
  if (showSuggestions.value) {
    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault()
        selectedSuggestionIndex.value = Math.min(
          selectedSuggestionIndex.value + 1,
          suggestionsList.value.length - 1
        )
        break
      case 'ArrowUp':
        event.preventDefault()
        selectedSuggestionIndex.value = Math.max(selectedSuggestionIndex.value - 1, 0)
        break
      case 'Enter':
        event.preventDefault()
        if (suggestionsList.value[selectedSuggestionIndex.value]) {
          onSuggestionClick(suggestionsList.value[selectedSuggestionIndex.value])
        }
        break
      case 'Escape':
        event.preventDefault()
        hideSuggestions()
        break
    }
    return
  }

  // 处理 Enter 和 Shift+Enter
  if (event.key === 'Enter') {
    if (!event.shiftKey) {
      // 普通 Enter：发送消息
      event.preventDefault()
      sendMessage()
    }
    // Shift+Enter：保持默认行为（换行）
  }
}

// 显示建议下拉框
const showSuggestionsDropdown = (textarea: HTMLTextAreaElement) => {
  const rect = textarea.getBoundingClientRect()
  const lineHeight = 24 // 估算行高
  const padding = 16
  
  // 计算大致的光标位置
  const lines = textarea.value.substring(0, textarea.selectionStart).split('\n').length
  const top = rect.top + padding + (lines - 1) * lineHeight + lineHeight
  
  suggestionsPosition.value = {
    top: Math.min(top, window.innerHeight - 300), // 确保不超出屏幕
    left: rect.left + padding
  }
  
  showSuggestions.value = true
}

// 隐藏建议
const hideSuggestions = () => {
  showSuggestions.value = false
  suggestionsList.value = []
  selectedSuggestionIndex.value = 0
  currentAtQuery.value = ''
}

// 搜索建议
const searchSuggestions = async (query: string) => {
  try {
    isSearchingVideos.value = true
    suggestionsList.value = []

    // 同时搜索课程和视频
    const [courseResponse, videoResponse] = await Promise.all([
      courseService.getStudentCourses({ search: query, page: 1, pageSize: 5 }), // 修改：使用学生课程API
      videoService.searchVideos({ keyword: query, page: 1, size: 5 })
    ])

    const suggestions: any[] = []

    // 添加课程建议
    if (courseResponse.data.code === 200 && courseResponse.data.data.list) {
      courseResponse.data.data.list.forEach((course: any) => {
        suggestions.push({
          id: course.id,
          type: 'course',
          name: course.name,
          description: course.description
        })
      })
    }

    // 添加视频建议
    if (videoResponse.data.code === 200 && videoResponse.data.data.list) {
      videoResponse.data.data.list.forEach((video: any) => {
        suggestions.push({
          id: video.id,
          type: 'video',
          name: video.title,
          description: video.description,
          courseName: video.course_name,
          courseId: video.course_id // 确保包含courseId
        })
      })
    }

    suggestionsList.value = suggestions
    selectedSuggestionIndex.value = 0
  } catch (error: any) {
    console.error('搜索建议失败:', error)
    // 添加错误处理，给用户友好的提示
    if (error.response && error.response.status === 401) {
      console.warn('用户未登录，无法获取课程列表')
    }
  } finally {
    isSearchingVideos.value = false
  }
}

// 处理建议点击
const onSuggestionClick = (suggestion: any) => {
  if (!textareaRef.value) return

  const textarea = textareaRef.value as any
  // 对于 Vuetify 的 v-textarea，需要访问内部的 textarea 元素
  const textareaElement = textarea.$el ? textarea.$el.querySelector('textarea') : textarea
  if (!textareaElement) return

  // 替换 @ 查询部分
  const beforeAt = userInput.value.substring(0, atStartPosition.value)
  const afterQuery = userInput.value.substring(atStartPosition.value + 1 + currentAtQuery.value.length)
  
  userInput.value = beforeAt + `@${suggestion.name} ` + afterQuery

  // 设置光标位置
  const newPosition = beforeAt.length + suggestion.name.length + 2
  nextTick(() => {
    textareaElement.focus()
    textareaElement.setSelectionRange(newPosition, newPosition)
  })
  // 添加到引用列表（避免重复）
  const existingRef = selectedReferences.value.find(ref => 
    ref.type === suggestion.type && ref.id === suggestion.id
  )
  
  if (!existingRef) {
    if (suggestion.type === 'course') {
      selectedReferences.value.push({
        id: suggestion.id,
        type: 'course',
        name: suggestion.name,
        description: suggestion.description
      })
    } else if (suggestion.type === 'video') {
      selectedReferences.value.push({
        id: suggestion.id,
        type: 'video',
        name: suggestion.name,
        description: suggestion.description,
        courseName: suggestion.courseName,
        courseId: suggestion.courseId // 如果有的话
      })
    }
    
    // 智能更新问答模式
    updateQaMode()
  }

  hideSuggestions()
}

// 截断文本
const truncate = (text: string, length: number) => {
  if (!text) return ''
  return text.length > length ? text.substring(0, length) + '...' : text
}

onMounted(() => {
  loadChatHistory()
  scrollToBottom()
})

// 组件卸载前清理
onBeforeUnmount(() => {
  // 会话清理由聊天历史服务管理，无需在此处删除
})
</script>

<style scoped>
.ai-assistant {
  width: 100%;
  height: 100%;
}

.content-card {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  height: calc(100vh - 150px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chat-history {
  height: 100%;
  border-right: 1px solid #f0f0f0;
  overflow: hidden; /* 防止历史区域影响整体布局 */
}

.history-section {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.history-list {
  flex: 1;
  overflow-y: auto;
  max-height: calc(100vh - 300px); /* 限制历史列表最大高度 */
}

.new-chat-btn {
  text-transform: none;
}

.chat-title {
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chat-time {
  font-size: 12px;
  color: #95a5a6;
}

.chat-main {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden; /* 确保主聊天区域不会溢出 */
}

/* 状态栏样式 */
.status-bar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 8px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  position: relative;
  overflow: hidden;
}

.status-content {
  display: flex;
  align-items: center;
  font-size: 14px;
  z-index: 1;
  position: relative;
}

.status-text {
  font-weight: 500;
  margin-right: 16px;
}

.status-stats {
  display: flex;
  gap: 12px;
  margin-left: auto;
  font-size: 12px;
  opacity: 0.9;
}

.stats-item {
  background: rgba(255, 255, 255, 0.15);
  padding: 2px 8px;
  border-radius: 12px;
  font-weight: 500;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  height: 0; /* 重要：强制flexbox正确计算高度 */
  min-height: 200px; /* 设置最小高度 */
  max-height: calc(100vh - 400px); /* 设置最大高度，为输入框留出空间 */
}

.message-wrapper {
  margin-bottom: 20px;
}

.message-wrapper.user {
  display: flex;
  justify-content: flex-end;
}

.message-content {
  display: flex;
  align-items: flex-start;
  max-width: 80%;
}

.message-avatar {
  margin: 0 12px;
}

.message-bubble {
  background-color: #fff;
  border-radius: 12px;
  padding: 12px 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.user .message-bubble {
  background-color: #6f23d1;
  color: white;
}

.message-text {
  font-size: 14px;
  line-height: 1.5;
}

.message-time {
  font-size: 12px;
  color: #95a5a6;
  margin-top: 4px;
}

.user .message-time {
  color: rgba(255, 255, 255, 0.8);
}

.ai-input-row {
  display: flex;
  align-items: flex-end;
  padding: 16px;
  gap: 12px;
  background: #fff;
}
.ai-input-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: center;
  justify-content: flex-end;
  height: 100%;
}
.ai-input-btn-small {
  width: 32px;
  height: 32px;
  min-width: 32px;
  min-height: 32px;
  border-radius: 6px;
  margin: 0;
  padding: 0;
}
.ai-input-textarea-large {
  flex: 1;
  min-height: 48px;
  font-size: 16px;
  margin: 0 8px;
}
.ai-input-send-btn {
  width: 40px;
  height: 40px;
  min-width: 40px;
  min-height: 40px;
  border-radius: 10px;
  margin-left: 0;
  margin-bottom: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.typing {
  display: flex;
  align-items: center;
  padding: 12px 16px;
}

.dot {
  width: 8px;
  height: 8px;
  background-color: #95a5a6;
  border-radius: 50%;
  margin: 0 2px;
  animation: typing 1.4s infinite;
}

.dot:nth-child(2) {
  animation-delay: 0.2s;
}

.dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
  }
  30% {
    transform: translateY(-4px);
  }
}

/* 自定义滚动条 */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb {
  background: #c0c0c0;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
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

/* 修复生成过程中的换行问题 */
:deep(.markdown-body br) {
  margin-bottom: 0.5em;  /* 增加换行的间距 */
  display: block;
  content: "";
}

:deep(.markdown-body p) {
  margin-bottom: 1em;   /* 增加段落的下边距 */
  white-space: pre-wrap;  /* 保留空白和换行 */
}

:deep(.paragraph-spacer) {
  height: 0.75em;
  display: block;
}

/* 引用来源样式 */
.message-sources {
  margin-top: 12px;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
  padding-top: 8px;
}

.message-sources-toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
  color: #95a5a6;
  cursor: pointer;
  padding: 4px 0;
  transition: color 0.2s;
}

.message-sources-toggle:hover {
  color: #2980b9;
}

.message-sources-list {
  margin-top: 8px;
  max-height: 300px;
  overflow-y: auto;
  border-left: 2px solid #f0f0f0;
}

.source-item {
  display: flex;
  margin-bottom: 8px;
  padding: 8px;
  background-color: rgba(0, 0, 0, 0.02);
  border-radius: 6px;
}

.source-index {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 30px;
  height: 30px;
  background-color: #f1f1f1;
  border-radius: 50%;
  font-size: 12px;
  color: #2c3e50;
  font-weight: 500;
  margin-right: 12px;
}

.source-content {
  flex: 1;
}

.source-title {
  font-weight: 500;
  margin-bottom: 4px;
  font-size: 14px;
}

.source-time {
  font-size: 12px;
  color: #2980b9;
  margin-bottom: 4px;
}

.source-preview {
  font-size: 13px;
  color: #7f8c8d;
  background-color: rgba(0, 0, 0, 0.03);
  padding: 8px;
  border-radius: 4px;
  margin-bottom: 8px;
  max-height: 100px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-word;
}

/* Markdown 样式 */
:deep(.markdown-body) {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  line-height: 1.6;
}

:deep(.markdown-paragraph) {
  margin: 0.8em 0;
  line-height: 1.6;
}

:deep(.markdown-break) {
  display: block;
  margin: 0.3em 0;
}

:deep(.markdown-hardbreak) {
  display: block;
  margin: 0.5em 0;
}

:deep(.markdown-list) {
  margin: 0.5em 0;
  padding-left: 1.5em;
}

:deep(.markdown-list li) {
  margin: 0.3em 0;
  line-height: 1.5;
}

:deep(.markdown-body p) {
  margin: 0.5em 0;
  line-height: 1.6;
}

:deep(.markdown-body h1) {
  font-size: 1.5em;
  margin: 0.8em 0 0.5em;
  font-weight: 600;
}

:deep(.markdown-body h2) {
  font-size: 1.3em;
  margin: 0.8em 0 0.5em;
  font-weight: 600;
}

:deep(.markdown-body h3) {
  font-size: 1.2em;
  margin: 0.6em 0 0.4em;
  font-weight: 600;
}

:deep(.markdown-body h4) {
  font-size: 1.1em;
  margin: 0.5em 0 0.3em;
  font-weight: 600;
}

:deep(.markdown-body ul, .markdown-body ol) {
  padding-left: 1.5em;
  margin: 0.5em 0;
}

:deep(.markdown-body li) {
  margin: 0.2em 0;
  line-height: 1.5;
}

:deep(.markdown-body code) {
  font-family: SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace;
  padding: 0.1em 0.3em;
  background-color: rgba(0, 0, 0, 0.05);
  border-radius: 3px;
  font-size: 0.9em;
}

:deep(.markdown-body pre) {
  background-color: rgba(0, 0, 0, 0.04);
  border-radius: 4px;
  padding: 0.8em;
  overflow-x: auto;
  margin: 0.5em 0;
}

:deep(.markdown-body pre code) {
  background-color: transparent;
  padding: 0;
  display: block;
  font-size: 0.85em;
}

:deep(.markdown-body blockquote) {
  border-left: 3px solid #ddd;
  margin: 0.5em 0;
  padding: 0 0.5em;
  color: #555;
  font-style: italic;
}

:deep(.markdown-body img) {
  max-width: 100%;
  border-radius: 4px;
}

:deep(.markdown-body table) {
  border-collapse: collapse;
  width: 100%;
  margin: 0.8em 0;
}

:deep(.markdown-body th, .markdown-body td) {
  border: 1px solid #ddd;
  padding: 6px 10px;
  text-align: left;
}

:deep(.markdown-body th) {
  background-color: rgba(0, 0, 0, 0.04);
  font-weight: 600;
}

:deep(.markdown-body strong) {
  font-weight: 600;
}

:deep(.markdown-body em) {
  font-style: italic;
}

.empty-chat {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 400px;
  color: #95a5a6;
}

.empty-icon {
  margin-bottom: 16px;
}

.empty-text {
  font-size: 16px;
  font-weight: 500;
}

.chat-menu-btn {
  opacity: 0;
  transition: opacity 0.2s;
}

.v-list-item:hover .chat-menu-btn {
  opacity: 1;
}

.v-list-item.active .chat-menu-btn {
  opacity: 1;
}

/* 内容审核警告弹窗样式 */
.warning-content {
  line-height: 1.6;
}

.warning-content ul {
  margin: 0;
  padding-left: 1.2em;
}

.warning-content li {
  margin: 0.3em 0;
}

/* 问答模式选择样式 */
.chat-mode-selector {
  border-bottom: 1px solid #f0f0f0;
}

.chat-mode-selector .v-card {
  border: none !important;
  box-shadow: none !important;
}

/* 当前选择信息样式 */
.current-selection .v-card {
  background-color: #f8f9fa;
  border: 1px solid #e9ecef !important;
}

.selected-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.selected-info .text-caption {
  line-height: 1.3;
}

/* 输入容器样式 */
.input-container {
  position: relative;
  flex: 1;
}

/* @ 引用建议下拉框样式 */
.suggestions-dropdown {
  max-width: 400px;
  min-width: 300px;
}

.suggestions-card {
  border-radius: 8px;
  max-height: 300px;
  overflow-y: auto;
}

.suggestion-item {
  padding: 12px 16px;
  cursor: pointer;
  border-bottom: 1px solid #f0f0f0;
  transition: background-color 0.2s;
}

.suggestion-item:hover,
.suggestion-item.suggestion-selected {
  background-color: #f8f9fa;
}

.suggestion-item:last-child {
  border-bottom: none;
}

.suggestion-content {
  width: 100%;
}

.suggestion-header {
  display: flex;
  align-items: center;
  margin-bottom: 4px;
}

.suggestion-title {
  font-weight: 500;
  font-size: 14px;
}

.suggestion-description {
  font-size: 12px;
  color: #6c757d;
  margin-bottom: 2px;
  line-height: 1.3;
}

.suggestion-course {
  font-size: 11px;
  color: #28a745;
  font-style: italic;
}

.suggestion-loading {
  padding: 12px 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6c757d;
}

.suggestion-empty {
  padding: 12px 16px;
  text-align: center;
  color: #6c757d;
}

/* 上传图片预览样式 */
.ai-uploaded-thumb {
  position: relative;
  display: inline-block;
  margin-left: 8px;
}

.ai-thumb-img {
  width: 40px;
  height: 40px;
  object-fit: cover;
  border-radius: 6px;
  border: 1px solid #e0e0e0;
}

.ai-thumb-remove {
  position: absolute;
  top: -4px;
  right: -4px;
  background-color: #f44336 !important;
  color: white !important;
  width: 18px !important;
  height: 18px !important;
  min-width: 18px !important;
  min-height: 18px !important;
}

/* 修改 v-card-text 的样式 */
:deep(.v-card-text) {
  height: 100%;
  padding: 0 !important;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

:deep(.v-card-title) {
  flex-shrink: 0;
}

:deep(.v-divider) {
  flex-shrink: 0;
}

/* 确保行布局占满高度 */
:deep(.ma-0.fill-height) {
  height: 100%;
  min-height: 0;
}
</style>
