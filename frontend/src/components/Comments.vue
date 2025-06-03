<template>
  <div class="comments-container">
    <!-- 评论列表区域 -->
    <div class="comments-list-container">
      <!-- 评论标题卡片 -->
      <v-card variant="flat" class="mb-3 header-card" elevation="0">
        <v-card-text class="py-3 px-3">
          <div class="d-flex align-center">
            <div class="text-subtitle-1 font-weight-medium">评论 ({{ totalComments }})</div>
            <v-spacer></v-spacer>
            <v-btn-toggle
              v-model="sortBy"
              density="compact"
              color="primary"
              mandatory
              size="small"
              rounded="pill"
            >
              <v-btn value="time" variant="text" :ripple="false" size="small">最新</v-btn>
              <v-btn value="likes" variant="text" :ripple="false" size="small">最热</v-btn>
            </v-btn-toggle>
          </div>
        </v-card-text>
      </v-card>
      
      <!-- 加载状态 -->
      <v-card v-if="loading" variant="flat" class="mb-3 py-6" elevation="0">
        <div class="d-flex justify-center align-center">
          <v-progress-circular indeterminate color="primary" size="32" class="mr-2"></v-progress-circular>
          <span class="text-medium-emphasis text-body-2">加载评论中...</span>
        </div>
      </v-card>
      
      <!-- 错误状态 -->
      <v-card v-else-if="error" variant="flat" class="mb-3 py-6" elevation="0">
        <div class="text-center">
          <v-alert type="error" variant="tonal" class="mb-3 mx-3" density="compact">{{ error }}</v-alert>
          <v-btn @click="fetchComments" color="primary" variant="tonal" size="small">重试</v-btn>
        </div>
      </v-card>
      
      <!-- 空状态 -->
      <v-card v-else-if="comments.length === 0" variant="flat" class="mb-3 py-6" elevation="0">
        <div class="d-flex flex-column align-center">
          <v-icon color="grey" size="48" class="mb-3">mdi-comment-outline</v-icon>
          <span class="text-subtitle-1 text-grey">暂无评论</span>
          <span class="text-body-2 text-medium-emphasis mt-1">成为第一个评论的人吧！</span>
        </div>
      </v-card>
      
      <!-- 评论列表 -->
      <template v-else>
        <v-card 
          v-for="comment in comments"
          :key="comment.id"
          variant="flat"
          class="mb-3 comment-card"
          elevation="0"
        >
          <v-card-text class="pa-3">
            <div class="d-flex">
              <v-avatar class="me-3" size="36">
                <v-img :src="comment.avatar || '/temp_img/default_avatar.jpg'" :alt="comment.userName"></v-img>
              </v-avatar>
              
              <div class="flex-grow-1">
                <div class="d-flex justify-space-between align-center mb-2">
                  <div class="font-weight-medium text-body-2">{{ comment.userName }}</div>
                  <div class="text-caption text-medium-emphasis">{{ formatDate(comment.createTime) }}</div>
                </div>
                
                <div class="text-body-2 mb-3 comment-content">{{ comment.content }}</div>
                
                <div class="d-flex align-center mb-2">
                  <v-chip
                    v-if="comment.timePoint !== undefined && comment.timePoint !== null"
                    size="small"
                    color="primary"
                    variant="tonal"
                    class="me-3"
                    prepend-icon="mdi-clock-outline"
                    @click="jumpToTimepoint(comment.timePoint)"
                    style="cursor: pointer"
                  >
                    {{ formatTime(comment.timePoint) }}
                  </v-chip>
                  
                  <v-btn
                    variant="text"
                    size="small"
                    @click="replyToComment(comment)"
                    class="me-2"
                    color="primary"
                    density="compact"
                    prepend-icon="mdi-reply"
                  >
                    回复
                  </v-btn>
                  
                  <v-btn
                    variant="text"
                    size="small"
                    @click="likeComment(comment)"
                    :color="comment.liked ? 'error' : 'grey'"
                    density="compact"
                    prepend-icon="mdi-thumb-up"
                  >
                    {{ comment.likes }}
                  </v-btn>

                  <!-- 添加删除按钮,只对自己的评论显示 -->
                  <v-btn
                    v-if="comment.userId === currentUserId"
                    variant="text"
                    size="small"
                    color="error"
                    density="compact"
                    class="ms-2"
                    prepend-icon="mdi-delete"
                    @click="showDeleteConfirm(comment)"
                  >
                    删除
                  </v-btn>
                </div>
                
                <!-- 回复列表 -->
                <div v-if="comment.replies && comment.replies.length > 0" class="replies-section">
                  <v-divider class="my-3"></v-divider>
                  
                  <div v-for="reply in comment.replies" :key="reply.id" class="reply-item mb-3">
                    <div class="d-flex">
                      <v-avatar size="28" class="me-2">
                        <v-img :src="reply.avatar || '/temp_img/default_avatar.jpg'" :alt="reply.userName"></v-img>
                      </v-avatar>
                      
                      <div class="flex-grow-1">
                        <div class="d-flex justify-space-between align-center mb-1">
                          <div class="font-weight-medium text-caption">{{ reply.userName }}</div>
                          <div class="text-caption text-medium-emphasis">{{ formatDate(reply.createTime) }}</div>
                        </div>
                        
                        <div class="text-caption mb-2 reply-content">{{ reply.content }}</div>
                        
                        <div class="d-flex align-center">
                          <v-btn
                            variant="text"
                            size="x-small"
                            @click="likeComment(reply)"
                            :color="reply.liked ? 'error' : 'grey'"
                            density="compact"
                            prepend-icon="mdi-thumb-up"
                          >
                            {{ reply.likes }}
                          </v-btn>

                          <!-- 添加删除按钮 -->
                          <v-btn
                            v-if="reply.userId === currentUserId"
                            variant="text"
                            size="x-small"
                            color="error"
                            density="compact"
                            class="ms-2"
                            prepend-icon="mdi-delete"
                            @click="showDeleteConfirm(reply)"
                          >
                            删除
                          </v-btn>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                
                <!-- 回复输入框 -->
                <div v-if="replyingTo === comment.id" class="reply-input-section mt-3">
                  <v-divider class="mb-3"></v-divider>
                  <v-card variant="outlined" class="reply-input-card">
                    <v-card-text class="pa-3">
                      <v-textarea
                        v-model="replyContent"
                        placeholder="回复..."
                        rows="2"
                        auto-grow
                        variant="outlined"
                        hide-details
                        density="compact"
                        ref="replyInput"
                        class="mb-3"
                      ></v-textarea>
                      
                      <div class="d-flex justify-end">
                        <v-btn
                          variant="text"
                          @click="cancelReply"
                          class="me-2"
                          size="small"
                        >
                          取消
                        </v-btn>
                        
                        <v-btn
                          color="primary"
                          :disabled="!replyContent.trim()"
                          @click="postReply(comment.id)"
                          size="small"
                        >
                          回复
                        </v-btn>
                      </div>
                    </v-card-text>
                  </v-card>
                </div>
              </div>
            </div>
          </v-card-text>
        </v-card>
        
        <!-- 加载更多按钮 -->
        <div v-if="hasMoreComments" class="text-center mt-3 mb-6">
          <v-btn
            variant="outlined"
            color="primary"
            @click="loadMoreComments"
            :loading="loadingMore"
            size="small"
            rounded="pill"
          >
            加载更多评论
          </v-btn>
        </div>
      </template>
    </div>
    
    <!-- 评论输入区域 -->
    <div class="comments-input-container">
      <v-divider></v-divider>
      
      <div class="input-area pa-4">
        <!-- 回复提示 -->
        <div v-if="replyingTo" class="reply-indicator mb-2 d-flex align-center">
          <span class="text-caption">
            回复 <span class="font-weight-medium">{{ replyingTo.userName }}</span>
          </span>
          <v-spacer></v-spacer>
          <v-btn
            variant="text"
            density="compact"
            size="small"
            @click="cancelReply"
            class="ms-2"
          >
            取消回复
          </v-btn>
        </div>

        <!-- 工具栏 -->
        <div class="tools-bar mb-2">
          <!-- 表情按钮和选择器 -->
          <v-menu
            v-model="showEmojiPicker"
            :close-on-content-click="false"
            location="top"
            :z-index="9999"
            offset-y
            min-width="360"
            transition="slide-y-transition"
          >
            <template v-slot:activator="{ props }">
              <v-btn
                icon="mdi-emoticon-outline"
                variant="text"
                size="small"
                v-bind="props"
                class="tool-button"
              ></v-btn>
            </template>

            <v-card class="emoji-menu-card">
              <v-card-text>
                <div class="emoji-category mb-4">
                  <div class="text-subtitle-2 mb-2">最近使用</div>
                  <div class="emoji-grid">
                    <v-btn
                      v-for="emoji in emojis.slice(0, 16)"
                      :key="emoji"
                      variant="text"
                      size="x-small"
                      class="emoji-btn pa-0"
                      @click="onEmojiSelect(emoji)"
                    >
                      {{ emoji }}
                    </v-btn>
                  </div>
                </div>

                <v-divider class="mb-4"></v-divider>

                <div class="emoji-category">
                  <div class="text-subtitle-2 mb-2">所有表情</div>
                  <div class="emoji-grid">
                    <v-btn
                      v-for="emoji in emojis"
                      :key="emoji"
                      variant="text"
                      size="x-small"
                      class="emoji-btn pa-0"
                      @click="onEmojiSelect(emoji)"
                    >
                      {{ emoji }}
                    </v-btn>
                  </div>
                </div>
              </v-card-text>
            </v-card>
          </v-menu>

          <!-- 图片上传按钮 -->
          <v-btn
            icon="mdi-image-outline"
            variant="text"
            size="small"
            @click="triggerImageUpload"
            class="tool-button ms-2"
          ></v-btn>
          
          <input
            type="file"
            ref="imageInput"
            accept="image/*"
            multiple
            class="d-none"
            @change="handleImageUpload"
          >
          
          <!-- 时间戳选择器只在非回复时显示 -->
          <v-checkbox
            v-if="showTimepointSelector && !replyingTo"
            v-model="addTimepoint"
            density="compact"
            hide-details
            color="primary"
            class="ms-2"
          >
            <template v-slot:label>
              <span class="text-body-2">在 </span>
              <v-chip size="small" color="primary" variant="tonal" class="mx-1">{{ formatCurrentTime }}</v-chip>
              <span class="text-body-2"> 添加时间戳</span>
            </template>
          </v-checkbox>
        </div>

        <!-- 输入框 -->
        <div class="comment-input-wrapper">
          <v-textarea
            v-model="newComment"
            placeholder="添加一条评论..."
            rows="2"
            auto-grow
            variant="outlined"
            hide-details
            density="compact"
            ref="commentInput"
            @focus="showTimepointSelector = true"
            class="mb-3"
          ></v-textarea>

          <!-- 图片预览 -->
          <div v-if="selectedImages.length > 0" class="image-preview-container mb-3">
            <div v-for="(image, index) in selectedImages" :key="index" class="image-preview-item">
              <v-img :src="image.url" aspect-ratio="1" cover class="rounded"></v-img>
              <v-btn
                icon="mdi-close"
                size="x-small"
                color="error"
                class="remove-image-btn"
                @click="removeImage(index)"
              ></v-btn>
            </div>
          </div>

          <!-- 发布按钮 -->
          <div class="d-flex justify-end">
            <v-btn
              color="primary"
              :disabled="!newComment.trim() && selectedImages.length === 0"
              @click="postComment"
              size="small"
              rounded="pill"
            >
              发布评论
            </v-btn>
          </div>
        </div>
      </div>
    </div>

    <!-- 添加删除确认对话框 -->
    <v-dialog v-model="showDeleteDialog" max-width="300">
      <v-card>
        <v-card-title class="text-subtitle-1 pa-4">
          确认删除
        </v-card-title>
        
        <v-card-text class="pb-2">
          确定要删除这条评论吗？此操作无法撤销。
        </v-card-text>
        
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn
            variant="text"
            @click="showDeleteDialog = false"
          >
            取消
          </v-btn>
          <v-btn
            color="error"
            variant="tonal"
            @click="deleteComment"
          >
            删除
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick, computed, onBeforeUnmount } from 'vue';
import videoService from '../api/videoService';
import { formatTimeFromSeconds } from '../utils/timeFormatter';

// 表情数组
const emojis = ['😀', '😂', '🤣', '😊', '😍', '🥰', '😘', '😋', '😎', '🤩', '😏', '😮', '🥺', '😢', '😭', '😤', '😠', '😡', '🤔', '🤗', '🤫', '🤭', '🥳', '😌', '😔', '😪', '🤤', '😴', '🥴', '😵', '🤯', '🤠', '🥸', '😷', '🤒', '🤕', '🤢', '🤮', '🤧', '😇', '🥳', '🥺', '🤓', '😎', '🤡', '👻', '👽', '👾', '🤖', '💩', '😺', '😸', '😹', '😻', '😼', '😽', '🙀', '😿', '😾', '❤️', '🧡', '💛', '💚', '💙', '💜', '🤎', '🖤', '🤍', '💯', '💢', '💥', '💫', '💦', '💨', '🕳️', '💣', '💬', '👁️‍🗨️', '🗨️', '🗯️', '💭', '💤'];

// 属性
const props = defineProps({
  videoId: {
    type: String,
    required: true
  },
  currentTime: {
    type: Number,
    default: 0
  }
});

// 事件
const emit = defineEmits(['jump-to-timepoint']);

// 状态
const comments = ref<any[]>([]);
const totalComments = ref(0);
const loading = ref(false);
const loadingMore = ref(false);
const error = ref<string | null>(null);
const page = ref(1);
const pageSize = ref(10);
const hasMoreComments = ref(false);
const sortBy = ref('time'); // 'time' or 'likes'

// 评论相关
const newComment = ref('');
const showTimepointSelector = ref(false);
const addTimepoint = ref(true);
const commentInput = ref<HTMLTextAreaElement | null>(null);

// 回复相关
const replyingTo = ref<{ id: number; userName: string } | null>(null);
const replyContent = ref('');
const replyInput = ref<HTMLTextAreaElement | null>(null);

// 新增状态
const showEmojiPicker = ref(false);
const selectedImages = ref<{ file: File; url: string }[]>([]);
const imageInput = ref<HTMLInputElement | null>(null);

// 删除相关
const currentUserId = ref(localStorage.getItem('wendao_user_id')); // 从localStorage获取当前用户ID
const showDeleteDialog = ref(false);
const commentToDelete = ref<any>(null);

// 计算属性: 格式化当前时间
const formatCurrentTime = computed(() => {
  return formatTime(props.currentTime);
});

// 方法
const fetchComments = async (resetPage = true) => {
  if (!props.videoId) return;
  
  if (resetPage) {
    page.value = 1;
    comments.value = [];
    loading.value = true;
  } else {
    loadingMore.value = true;
  }
  
  error.value = null;
  
  try {
    const result = await videoService.getVideoComments(props.videoId, {
      page: page.value,
      pageSize: pageSize.value,
      sortBy: sortBy.value
    });
    
    if (result.data.code === 200) {
      const responseData = result.data.data; // 确保正确获取data字段
      
      if (resetPage) {
        comments.value = responseData.list || [];
      } else {
        comments.value = [...comments.value, ...(responseData.list || [])];
      }
      
      // 更新总评论数，确保从正确的数据结构中获取
      totalComments.value = responseData.total || 0;
      hasMoreComments.value = comments.value.length < (responseData.total || 0);
    } else {
      throw new Error(result.data.message || '获取评论失败');
    }
  } catch (err: any) {
    error.value = err.message || '获取评论失败';
    totalComments.value = 0; // 发生错误时重置评论数
  } finally {
    loading.value = false;
    loadingMore.value = false;
  }
};

const loadMoreComments = () => {
  page.value += 1;
  fetchComments(false);
};

// 监听排序方式变化
watch(sortBy, () => {
  fetchComments(true);
});

// 表情选择处理
const onEmojiSelect = (emoji: string) => {
  newComment.value += emoji;
  // 不关闭选择器，让用户可以继续选择
};

// 添加点击外部关闭表情选择器的处理
const handleClickOutside = (event: MouseEvent) => {
  const wrapper = document.querySelector('.comment-input-wrapper');
  const target = event.target as HTMLElement;
  if (showEmojiPicker.value && wrapper && !wrapper.contains(target)) {
    showEmojiPicker.value = false;
  }
};

// 图片上传相关
const triggerImageUpload = () => {
  imageInput.value?.click();
};

const handleImageUpload = (event: Event) => {
  const input = event.target as HTMLInputElement;
  if (!input.files?.length) return;

  const files = Array.from(input.files);
  const maxSize = 5 * 1024 * 1024; // 5MB
  const maxImages = 9;

  files.forEach(file => {
    if (selectedImages.value.length >= maxImages) {
      alert('最多只能上传9张图片');
      return;
    }

    if (file.size > maxSize) {
      alert('图片大小不能超过5MB');
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      selectedImages.value.push({
        file,
        url: e.target?.result as string
      });
    };
    reader.readAsDataURL(file);
  });

  // 清空input，允许重复选择相同文件
  input.value = '';
};

const removeImage = (index: number) => {
  selectedImages.value.splice(index, 1);
};

// 修改发布评论方法
const postComment = async () => {
  if (!props.videoId || (!newComment.value.trim() && selectedImages.value.length === 0)) return;
  
  try {
    const formData = new FormData();
    formData.append('content', newComment.value.trim());
    
    // 如果是回复，添加父评论ID
    if (replyingTo.value) {
      formData.append('parentId', replyingTo.value.id.toString());
    } else if (addTimepoint.value) {
      // 只有不是回复时才添加时间戳
      formData.append('timePoint', props.currentTime.toString());
    }
    
    // 添加图片
    selectedImages.value.forEach((image, index) => {
      formData.append(`images`, image.file);
    });
    
    const result = await videoService.addVideoComment(props.videoId, formData);
    
    if (result.data.code === 200) {
      // 重置输入
      newComment.value = '';
      selectedImages.value = [];
      showTimepointSelector.value = false;
      replyingTo.value = null;
      
      // 刷新评论列表
      fetchComments(true);
    } else {
      throw new Error(result.data.message || '发布评论失败');
    }
  } catch (err: any) {
    console.error('发布评论失败:', err);
    alert('发布评论失败: ' + (err.message || '未知错误'));
  }
};

// 修改回复评论方法
const replyToComment = (comment: any) => {
  replyingTo.value = {
    id: comment.id,
    userName: comment.userName
  };
  newComment.value = `@${comment.userName} `;
  
  // 聚焦主输入框
  nextTick(() => {
    if (commentInput.value) {
      commentInput.value.focus();
    }
  });
  
  // 滚动到输入框
  const inputContainer = document.querySelector('.comments-input-container');
  if (inputContainer) {
    inputContainer.scrollIntoView({ behavior: 'smooth' });
  }
};

// 取消回复
const cancelReply = () => {
  replyingTo.value = null;
  newComment.value = '';
};

const postReply = async (commentId: string) => {
  if (!props.videoId || !replyContent.value.trim()) return;
  
  try {
    const replyData = {
      content: replyContent.value.trim(),
      parentId: commentId
    };
    
    const result = await videoService.addVideoComment(props.videoId, replyData);
    
    if (result.data.code === 200) {
      // 重置输入和状态
      cancelReply();
      
      // 刷新评论列表
      fetchComments(true);
    } else {
      throw new Error(result.data.message || '发布回复失败');
    }
  } catch (err: any) {
    console.error('发布回复失败:', err);
    alert('发布回复失败: ' + (err.message || '未知错误'));
  }
};

const likeComment = async (comment: any) => {
  try {
    // 在发送请求前,先预更新UI状态
    const isLiked = comment.liked;
    comment.liked = !isLiked;
    comment.likes += isLiked ? -1 : 1;

    // 调用后端API进行点赞
    const result = await videoService.likeComment(comment.id, {});
    
    if (result.data.code === 200) {
      // 使用后端返回的实际数据更新状态
      comment.likes = result.data.data.likes;
      comment.liked = result.data.data.liked;
    } else {
      // 如果请求失败,恢复到原始状态
      comment.liked = isLiked;
      comment.likes += isLiked ? 1 : -1;
      throw new Error(result.data.message || '点赞失败');
    }
  } catch (err: any) {
    console.error('点赞操作失败:', err);
    
    // 如果出错，显示错误信息
    let errorMessage = '点赞失败';
    if (err.response && err.response.data && err.response.data.message) {
      errorMessage = err.response.data.message;
    } else if (err.message) {
      errorMessage = err.message;
    }
    
    alert(errorMessage);
  }
};

const jumpToTimepoint = (seconds: number) => {
  emit('jump-to-timepoint', seconds);
};

const formatTime = (seconds: number) => {
  return formatTimeFromSeconds(seconds);
};

const formatDate = (dateString: string) => {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSec = Math.floor(diffMs / 1000);
  
  if (diffSec < 60) {
    return '刚刚';
  } else if (diffSec < 3600) {
    return `${Math.floor(diffSec / 60)}分钟前`;
  } else if (diffSec < 86400) {
    return `${Math.floor(diffSec / 3600)}小时前`;
  } else if (diffSec < 2592000) {
    return `${Math.floor(diffSec / 86400)}天前`;
  } else {
    return date.toLocaleDateString();
  }
};

// 监听 videoId 变化，重新获取评论
watch(() => props.videoId, (newId) => {
  if (newId) {
    fetchComments(true);
  }
});

// 删除评论方法
const deleteComment = async () => {
  if (!commentToDelete.value) return;
  
  try {
    const result = await videoService.deleteComment(commentToDelete.value.id);
    
    if (result.data.code === 200) {
      // 刷新评论列表
      fetchComments(true);
      showDeleteDialog.value = false;
      commentToDelete.value = null;
    } else {
      throw new Error(result.data.message || '删除评论失败');
    }
  } catch (error) {
    console.error('删除评论失败:', error);
    let errorMessage = '删除评论失败';
    
    if (error instanceof Error) {
      if (error.message) {
        errorMessage = error.message;
      }
    } else if (typeof error === 'object' && error !== null) {
      const err = error as any;
      if (err.response) {
        if (err.response.status === 403) {
          errorMessage = '您没有权限删除此评论';
        } else if (err.response.status === 404) {
          errorMessage = '评论不存在或已被删除';
        } else if (err.response.data && err.response.data.message) {
          errorMessage = err.response.data.message;
        } else if (err.response.status === 0 || err.code === 'ERR_NETWORK') {
          errorMessage = '网络错误，请检查网络连接';
        }
      }
    }
    
    // 显示错误提示
    alert(errorMessage);
  } finally {
    // 无论成功失败都关闭对话框
    showDeleteDialog.value = false;
  }
};

// 显示删除确认对话框
const showDeleteConfirm = (comment: any) => {
  commentToDelete.value = comment;
  showDeleteDialog.value = true;
};

// 生命周期钩子
onMounted(() => {
  document.addEventListener('click', handleClickOutside);
  if (props.videoId) {
    fetchComments(true);
  }
  window.addEventListener('resize', () => {
    if (showEmojiPicker.value) {
      showEmojiPicker.value = false;
    }
  });
});

// 在组件卸载时移除事件监听
onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside);
  window.removeEventListener('resize', () => {
    if (showEmojiPicker.value) {
      showEmojiPicker.value = false;
    }
  });
});
</script>

<style scoped>
.comments-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: visible !important; /* 修改这里，允许内容溢出 */
}

.comments-list-container {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
  padding-right: 4px;
  position: relative; /* 添加相对定位 */
}

.comments-input-container {
  margin-top: auto;
  background-color: white;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
  padding: 16px;
}

/* 输入区域的整体容器 */
.input-area {
  position: relative;
}

/* 工具栏样式 */
.tools-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

/* 表情选择器容器 */
.emoji-menu-card {
  max-height: 400px;
  overflow-y: auto;
  border-radius: 8px;
  background-color: white;
  transition: none;
}

.emoji-grid {
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  gap: 4px;
}

.emoji-btn {
  min-width: 36px !important;
  width: 36px !important;
  height: 36px !important;
  font-size: 20px !important;
  border-radius: 4px !important;
}

.emoji-btn:hover {
  background-color: rgba(0, 0, 0, 0.04) !important;
}

.tool-button {
  width: 32px;
  height: 32px;
}

/* 确保菜单显示在最上层 */
:deep(.v-overlay) {
  z-index: 9999 !important;
}

:deep(.v-menu) {
  z-index: 9999 !important;
}

/* 修改表情选择器的样式 */
:deep(.v-menu__content) {
  transition: none !important;
  box-shadow: 0 4px 25px 0 rgba(0, 0, 0, 0.1) !important;
}

:deep(.v-menu__content--active) {
  transform: translateY(0) !important;
  opacity: 1 !important;
}

:deep(.v-menu__content:not(.v-menu__content--active)) {
  transform: translateY(8px) !important;
  opacity: 0 !important;
  pointer-events: none !important;
}

/* 输入框样式 */
.comment-input-wrapper {
  background-color: white;
  border-radius: 4px;
}

/* 图片预览区域 */
.image-preview-container {
  margin-top: 8px;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
  gap: 8px;
  padding: 8px;
  background-color: rgba(0, 0, 0, 0.02);
  border-radius: 8px;
}

.image-preview-item {
  position: relative;
  aspect-ratio: 1;
}

.remove-image-btn {
  position: absolute !important;
  top: -8px !important;
  right: -8px !important;
  background-color: white !important;
}

/* 卡片样式 */
.header-card {
  background-color: white;
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 12px;
}

.comment-card {
  background-color: white;
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 12px;
  transition: all 0.2s ease;
}

.comment-card:hover {
  border-color: rgba(var(--v-theme-primary), 0.2);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.input-card {
  position: relative;
  z-index: 1001;
}

.reply-input-card {
  background-color: #f8f9fa;
  border: 1px solid rgba(var(--v-theme-primary), 0.2);
  border-radius: 8px;
}

/* 内容样式 */
.comment-content {
  line-height: 1.5;
  word-break: break-word;
}

.reply-content {
  line-height: 1.4;
  word-break: break-word;
  color: rgba(0, 0, 0, 0.8);
}

.replies-section {
  background-color: rgba(0, 0, 0, 0.02);
  border-radius: 8px;
  padding: 12px;
  margin-top: 8px;
}

.reply-item {
  padding: 8px 0;
}

.reply-item:not(:last-child) {
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.reply-input-section {
  background-color: rgba(var(--v-theme-primary), 0.02);
  border-radius: 8px;
  padding: 12px;
}

/* 头像样式 */
.v-avatar {
  border: 2px solid rgba(0, 0, 0, 0.08);
}

/* 按钮样式优化 */
.v-btn {
  text-transform: none;
  font-weight: 500;
}

.v-btn--size-small {
  min-height: 32px;
}

/* Chip样式 */
.v-chip {
  font-weight: 500;
}

.v-chip--size-small {
  height: 28px;
}

/* 响应式优化 */
@media (max-width: 768px) {
  .comments-list-container {
    padding: 6px;
  }
  
  .comment-card,
  .header-card {
    border-radius: 8px;
  }
  
  .v-avatar {
    width: 32px !important;
    height: 32px !important;
  }
  
  .replies-section .v-avatar {
    width: 24px !important;
    height: 24px !important;
  }
}

/* 自定义滚动条 */
.comments-list-container::-webkit-scrollbar {
  width: 4px;
}

.comments-list-container::-webkit-scrollbar-track {
  background: transparent;
}

.comments-list-container::-webkit-scrollbar-thumb {
  background-color: rgba(0, 0, 0, 0.15);
  border-radius: 2px;
}

.comments-list-container::-webkit-scrollbar-thumb:hover {
  background-color: rgba(0, 0, 0, 0.25);
}

/* 动画效果 */
.comment-card {
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 焦点状态优化 */
.v-textarea:focus-within {
  box-shadow: 0 0 0 2px rgba(var(--v-theme-primary), 0.2);
}

/* 时间戳芯片特殊样式 */
.v-chip[style*="cursor: pointer"]:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(var(--v-theme-primary), 0.3);
}

/* 新增样式 */
.image-preview-container {
  margin-top: 8px;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
  gap: 8px;
  padding: 8px;
  background-color: rgba(0, 0, 0, 0.02);
  border-radius: 8px;
}

.image-preview-item {
  position: relative;
  aspect-ratio: 1;
}

.remove-image-btn {
  position: absolute !important;
  top: -8px !important;
  right: -8px !important;
  background-color: white !important;
}

/* 响应式优化 */
@media (max-width: 768px) {
  .image-preview-container {
    grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
  }
}

/* 调整滚动区域的样式 */
.sidebar-content {
  position: relative;
  z-index: 999;
}

/* 确保窗口项内容可以正确滚动 */
.window-item {
  position: relative;
  z-index: 999;
}

.reply-indicator {
  background-color: rgba(var(--v-theme-primary), 0.05);
  border-radius: 8px;
  padding: 8px 12px;
}

/* 删除按钮样式 */
.v-btn.error {
  opacity: 0.8;
}

.v-btn.error:hover {
  opacity: 1;
}

/* 表情选择器动画 */
.slide-y-transition-enter-active,
.slide-y-transition-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.slide-y-transition-enter-from,
.slide-y-transition-leave-to {
  opacity: 0;
  transform: translateY(15px);
}

:deep(.v-menu__content) {
  transition: none !important;
  box-shadow: 0 4px 25px 0 rgba(0, 0, 0, 0.1) !important;
}

.emoji-menu-card {
  max-height: 400px;
  overflow-y: auto;
  border-radius: 8px;
  background-color: white;
  transition: none;
}
</style>