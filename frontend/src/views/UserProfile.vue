<template>
  <v-container class="profile-container py-8">
    <!-- 页面标题区域 -->
    <div class="page-header mb-8">
      <div class="d-flex align-center mb-4">
        <div class="header-icon">
          <v-icon size="32" color="primary">mdi-account-circle</v-icon>
        </div>
        <div class="ml-4">
          <h1 class="text-h3 font-weight-bold text-primary mb-1">个人资料</h1>
          <p class="text-h6 text-medium-emphasis mb-0">管理您的个人信息和账户设置</p>
        </div>
      </div>
    </div>
    
    <!-- 主要内容区域 -->
    <v-row>
      <!-- 基本信息卡片 -->
      <v-col cols="12" lg="7">
        <v-card class="profile-card mb-6" elevation="2">
          <v-card-title class="card-header">
            <div class="d-flex align-center">
              <v-icon color="primary" class="mr-3">mdi-account-edit</v-icon>
              <span class="text-h5 font-weight-bold">基本信息</span>
            </div>
          </v-card-title>
          
          <v-divider class="mx-6"></v-divider>
          
          <v-card-text class="px-6 py-8">
            <!-- 头像区域 -->
            <div class="avatar-section mb-8">
              <div class="d-flex flex-column flex-md-row align-center">
                <div class="avatar-wrapper">
                  <AvatarUpload
                    :username="userInfo.name"
                    :initialAvatar="userInfo.avatar"
                    :size="140"
                    @avatar-updated="handleAvatarUpdated"
                  />
                </div>
                <div class="ml-md-8 mt-6 mt-md-0 text-center text-md-start">
                  <h3 class="text-h5 font-weight-bold mb-2">个人头像</h3>
                  <div class="upload-tips">
                    <v-chip size="small" color="info" variant="tonal" class="mb-2">
                      <v-icon start size="small">mdi-information</v-icon>
                      支持格式
                    </v-chip>
                    <div class="text-body-2 text-medium-emphasis mb-2">
                      支持 JPG、PNG 或 GIF 格式的图片
                    </div>
                    <div class="text-body-2 text-medium-emphasis">
                      建议图片大小不超过 2MB，尺寸为 200x200 像素
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 用户信息表单 -->
            <div class="user-info-form">
              <v-row>
                <v-col cols="12" md="6">
                  <div class="form-field">
                    <label class="field-label">用户名</label>
                    <v-text-field
                      v-model="userInfo.name"
                      variant="outlined"
                      readonly
                      density="comfortable"
                      prepend-inner-icon="mdi-account"
                      class="profile-input"
                    ></v-text-field>
                  </div>
                </v-col>
                
                <v-col cols="12" md="6">
                  <div class="form-field">
                    <label class="field-label">用户角色</label>
                    <v-text-field
                      :value="roleName"
                      variant="outlined"
                      readonly
                      density="comfortable"
                      prepend-inner-icon="mdi-shield-account"
                      class="profile-input"
                    ></v-text-field>
                  </div>
                </v-col>
                
                <v-col cols="12">
                  <div class="form-field">
                    <label class="field-label">电子邮箱</label>
                    <v-text-field
                      v-model="userInfo.email"
                      variant="outlined"
                      readonly
                      density="comfortable"
                      prepend-inner-icon="mdi-email"
                      class="profile-input"
                    ></v-text-field>
                  </div>
                </v-col>
              </v-row>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      
      <!-- 密码管理卡片 -->
      <v-col cols="12" lg="5">
        <v-card class="password-card" elevation="2">
          <v-card-title class="card-header">
            <div class="d-flex align-center">
              <v-icon color="warning" class="mr-3">mdi-key-variant</v-icon>
              <span class="text-h5 font-weight-bold">密码管理</span>
            </div>
          </v-card-title>
          
          <v-divider class="mx-6"></v-divider>
          
          <v-card-text class="px-6 py-8">
            <div class="password-info mb-6">
              <v-alert
                type="info"
                variant="tonal"
                density="compact"
                class="mb-4"
              >
                <template v-slot:prepend>
                  <v-icon>mdi-shield-lock</v-icon>
                </template>
                定期更换密码有助于保护您的账户安全
              </v-alert>
            </div>
            
            <v-form @submit.prevent="changePassword">
              <div class="form-field mb-4">
                <label class="field-label">当前密码</label>
                <v-text-field
                  v-model="passwordForm.currentPassword"
                  type="password"
                  variant="outlined"
                  density="comfortable"
                  prepend-inner-icon="mdi-lock"
                  required
                  class="profile-input"
                ></v-text-field>
              </div>
              
              <div class="form-field mb-4">
                <label class="field-label">新密码</label>
                <v-text-field
                  v-model="passwordForm.newPassword"
                  type="password"
                  variant="outlined"
                  density="comfortable"
                  prepend-inner-icon="mdi-lock-plus"
                  required
                  hint="密码长度至少6位"
                  persistent-hint
                  class="profile-input"
                ></v-text-field>
              </div>
              
              <div class="form-field mb-6">
                <label class="field-label">确认新密码</label>
                <v-text-field
                  v-model="passwordForm.confirmPassword"
                  type="password"
                  variant="outlined"
                  density="comfortable"
                  prepend-inner-icon="mdi-lock-check"
                  required
                  :error-messages="passwordMismatch ? '两次输入的密码不一致' : ''"
                  class="profile-input"
                ></v-text-field>
              </div>
              
              <v-alert
                v-if="passwordChangeMessage"
                :type="passwordChangeSuccess ? 'success' : 'error'"
                variant="tonal"
                class="mb-6"
              >
                <template v-slot:prepend>
                  <v-icon>{{ passwordChangeSuccess ? 'mdi-check-circle' : 'mdi-alert-circle' }}</v-icon>
                </template>
                {{ passwordChangeMessage }}
              </v-alert>
              
              <div class="d-flex justify-end">
                <v-btn
                  color="primary"
                  type="submit"
                  :disabled="isPasswordChanging || passwordMismatch"
                  :loading="isPasswordChanging"
                  size="large"
                  elevation="2"
                  class="update-btn"
                >
                  <v-icon start>mdi-content-save</v-icon>
                  更新密码
                </v-btn>
              </div>
            </v-form>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import userService from '../api/userService';
import { useUserStore } from '../stores/userStore';
import AvatarUpload from '../components/AvatarUpload.vue';

const userStore = useUserStore();
const userInfo = ref({
  id: '',
  name: '',
  email: '',
  role: '',
  avatar: ''
});

const passwordForm = ref({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
});

const isPasswordChanging = ref(false);
const passwordChangeMessage = ref('');
const passwordChangeSuccess = ref(false);

// 计算属性
const passwordMismatch = computed(() => {
  return passwordForm.value.newPassword &&
         passwordForm.value.confirmPassword &&
         passwordForm.value.newPassword !== passwordForm.value.confirmPassword;
});

const roleName = computed(() => {
  const roleMap = {
    'teacher': '教师',
    'student': '学生',
    'admin': '管理员'
  };
  return roleMap[userInfo.value.role] || userInfo.value.role;
});

// 方法
const fetchUserInfo = async () => {
  try {
    const response = await userService.getUserInfo();
    if (response.data.code === 200) {
      userInfo.value = response.data.data;
      userStore.updateUserInfo(response.data.data);
    }
  } catch (error) {
    console.error('获取用户信息失败:', error);
  }
};

const handleAvatarUpdated = (newAvatarUrl) => {
  userInfo.value.avatar = newAvatarUrl;
};

const changePassword = async () => {
  if (passwordMismatch.value) {
    return;
  }
  
  isPasswordChanging.value = true;
  passwordChangeMessage.value = '';
  passwordChangeSuccess.value = false;
  
  try {
    const response = await userService.changePassword(
      passwordForm.value.currentPassword,
      passwordForm.value.newPassword
    );
    
    if (response.data.code === 200) {
      passwordChangeSuccess.value = true;
      passwordChangeMessage.value = '密码已成功更新';
      
      // 重置表单
      passwordForm.value = {
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
      };
    } else {
      passwordChangeMessage.value = response.data.message || '密码更新失败';
    }
  } catch (error) {
    passwordChangeMessage.value = error.message || '发生错误';
  } finally {
    isPasswordChanging.value = false;
  }
};

// 生命周期钩子
onMounted(() => {
  fetchUserInfo();
});
</script>

<style scoped>
.profile-container {
  max-width: 1400px;
  margin: 0 auto;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  min-height: 100vh;
  padding-top: 2rem;
}

/* 页面标题样式 */
.page-header {
  text-align: left;
  position: relative;
}

.header-icon {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 20px;
  padding: 16px;
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
}

/* 卡片样式 */
.profile-card, .password-card {
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.profile-card:hover, .password-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.15);
}

.card-header {
  background: linear-gradient(135deg, #f8f9ff 0%, #e3f2fd 100%);
  padding: 24px !important;
  border-radius: 24px 24px 0 0;
}

/* 头像区域样式 */
.avatar-section {
  background: linear-gradient(135deg, #f8f9ff 0%, #e8f5e8 100%);
  border-radius: 20px;
  padding: 32px;
  border: 2px dashed rgba(102, 126, 234, 0.2);
  transition: all 0.3s ease;
}

.avatar-section:hover {
  border-color: rgba(102, 126, 234, 0.4);
  background: linear-gradient(135deg, #f0f4ff 0%, #e0f7e0 100%);
}

.avatar-wrapper {
  position: relative;
}

.avatar-wrapper::after {
  content: '';
  position: absolute;
  top: -10px;
  left: -10px;
  right: -10px;
  bottom: -10px;
  background: linear-gradient(45deg, #667eea, #764ba2, #f093fb, #f5576c);
  border-radius: 50%;
  z-index: -1;
  opacity: 0.3;
  transition: opacity 0.3s ease;
}

.avatar-wrapper:hover::after {
  opacity: 0.6;
}

.upload-tips {
  max-width: 280px;
}

/* 表单样式 */
.form-field {
  margin-bottom: 1.5rem;
}

.field-label {
  display: block;
  font-weight: 600;
  color: #37474f;
  margin-bottom: 8px;
  font-size: 0.875rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.profile-input :deep(.v-field) {
  background: rgba(255, 255, 255, 0.8);
  border-radius: 16px;
  transition: all 0.3s ease;
}

.profile-input :deep(.v-field:hover) {
  background: rgba(255, 255, 255, 0.95);
  transform: translateY(-1px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.profile-input :deep(.v-field--focused) {
  background: rgba(255, 255, 255, 1);
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.2);
}

/* 密码信息样式 */
.password-info {
  background: linear-gradient(135deg, #fff3e0 0%, #fce4ec 100%);
  border-radius: 16px;
  padding: 20px;
  border: 1px solid rgba(255, 193, 7, 0.2);
}

/* 按钮样式 */
.update-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  border-radius: 16px;
  text-transform: none;
  font-weight: 600;
  padding: 0 32px;
  transition: all 0.3s ease;
}

.update-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.4);
}

.update-btn:active {
  transform: translateY(0);
}

/* 响应式设计 */
@media (max-width: 960px) {
  .profile-container {
    padding: 1rem;
  }
  
  .page-header h1 {
    font-size: 2rem;
  }
  
  .avatar-section {
    padding: 24px;
    text-align: center;
  }
  
  .card-header {
    padding: 20px !important;
  }
}

/* 动画效果 */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.profile-card, .password-card {
  animation: fadeInUp 0.6s ease-out;
}

.password-card {
  animation-delay: 0.2s;
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 8px;
}

::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.05);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
}
</style>
