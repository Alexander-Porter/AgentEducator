<!-- 知识图谱页面 -->
<template>
  <v-container fluid class="knowledge-map-container fill-height pa-4">
    <v-row>
      <v-col cols="12">
        <v-card class="mb-4" elevation="0">
          <v-card-text class="d-flex align-center py-2">
            <div>
              <h1 class="text-h4 font-weight-bold" style="color: #6f23d1;">知识图谱</h1>
              <p class="text-subtitle-1 text-medium-emphasis mt-1 mb-0">
                探索课程知识体系，掌握学习进度，提升专业能力
              </p>
            </div>
            
            <!-- 沉浸模式切换按钮 -->
            <v-spacer></v-spacer>
            <v-btn
              v-if="currentTab === 'knowledge'"
              :color="isImmersiveMode ? 'error' : 'primary'"
              :icon="isImmersiveMode ? 'mdi-fullscreen-exit' : 'mdi-fullscreen'"
              variant="outlined"
              @click="toggleImmersiveMode"
              class="mr-2"
            >
            </v-btn>
          </v-card-text>
        </v-card>
        
        <!-- 沉浸模式全屏遮罩 -->
        <v-overlay
          v-model="isImmersiveMode"
          class="immersive-overlay"
          z-index="9999"
          persistent
        >
          <v-fade-transition>
            <div v-if="isImmersiveMode" class="immersive-container">
              <!-- 沉浸模式头部控制栏 -->
              <div class="immersive-header">
                <div class="d-flex align-center">
                  <v-icon color="white" class="mr-2">mdi-graph</v-icon>
                  <span class="text-white text-h6">知识图谱 - 沉浸模式</span>
                </div>
                
                <!-- 筛选控件 -->
                <div class="d-flex align-center">
                  <v-text-field
                    v-model="nodeFilter"
                    placeholder="搜索节点..."
                    variant="outlined"
                    density="compact"
                    hide-details
                    prepend-inner-icon="mdi-magnify"
                    clearable
                    class="mr-4"
                    style="width: 300px;"
                    color="white"
                    bg-color="rgba(255,255,255,0.1)"
                  />
                  <v-btn
                    icon="mdi-fullscreen-exit"
                    color="white"
                    variant="text"
                    @click="exitImmersiveMode"
                  />
                </div>
              </div>
                <!-- 沉浸模式图谱容器 -->
              <div 
                id="immersive-graph-container" 
                class="immersive-graph"
                :style="{ height: 'calc(100vh - 80px)' }"
              ></div>
              
              <!-- 沉浸模式下的知识点详情 -->
              <v-slide-x-transition>
                <v-card 
                  v-if="isImmersiveMode && selectedNode" 
                  class="immersive-detail-card"
                  elevation="12"
                >
                  <v-card-title class="text-h6 pa-4 d-flex align-center">
                    <span class="flex-grow-1">{{ selectedNode.name }}</span>
                    <v-chip
                      :color="getNodeTypeColor(selectedNode.category || 0)"
                      size="small"
                      class="ml-2"
                    >
                      {{ getNodeTypeName(selectedNode.category || 0) }}
                    </v-chip>
                    <v-btn
                      icon="mdi-close"
                      variant="text"
                      size="small"
                      @click="selectedNode = null"
                      class="ml-2"
                    />
                  </v-card-title>
                  
                  <v-card-text class="pa-4 pt-0">
                    <v-divider class="mb-3" />
                    
                    <p class="text-body-1 mb-3">{{ selectedNode.description || '暂无描述' }}</p>
                    
                    <!-- 节点关系 -->
                    <div v-if="selectedNode && nodeFeatures.length > 0" class="mb-4">
                      <div class="d-flex align-center mb-2">
                        <v-icon color="primary" class="mr-2">mdi-star-outline</v-icon>
                        <span class="text-subtitle-2 font-weight-medium">知识点关系</span>
                      </div>
                      <v-list density="compact" class="bg-transparent pa-0">
                        <v-list-item
                          v-for="(feature, index) in nodeFeatures"
                          :key="index"
                          class="px-0"
                        >
                          <template v-slot:prepend>
                            <v-icon size="small" :color="getRelationConfig(feature.type).color" class="mr-2">
                              mdi-arrow-right-thin
                            </v-icon>
                          </template>
                          <v-list-item-title class="text-body-2">
                            {{ feature.description }}
                          </v-list-item-title>
                        </v-list-item>
                      </v-list>
                    </div>
                    
                    <!-- 边的描述信息 -->
                    <div v-if="selectedEdgeInfo" class="mb-4">
                      <div class="d-flex align-center mb-2">
                        <v-icon color="primary" class="mr-2">mdi-arrow-decision</v-icon>
                        <span class="text-subtitle-2 font-weight-medium">关系描述</span>
                      </div>
                      <v-card variant="outlined" class="pa-3">
                        <div class="d-flex align-center mb-2">
                          <span class="text-body-2">{{ selectedEdgeInfo.source }} → {{ selectedEdgeInfo.target }}</span>
                          <v-chip
                            :color="getRelationConfig(selectedEdgeInfo.relation_type || 'related').color"
                            size="small"
                            class="ml-2"
                          >
                            {{ getRelationConfig(selectedEdgeInfo.relation_type || 'related').name }}
                          </v-chip>
                        </div>
                        <p class="text-body-2 mb-0">{{ selectedEdgeInfo.description || '暂无关系描述' }}</p>
                      </v-card>
                    </div>
                    
                    <!-- 相关视频列表 -->
                    <div v-if="selectedNode.relatedVideos?.length" class="mb-4">
                      <div class="d-flex align-center justify-space-between mb-2">
                        <div class="d-flex align-center">
                          <v-icon color="primary" class="mr-2">mdi-video-outline</v-icon>
                          <span class="text-subtitle-2 font-weight-medium">相关视频</span>
                        </div>
                        <v-btn
                          color="primary"
                          size="small"
                          variant="text"
                          prepend-icon="mdi-robot"
                          @click="askAI(selectedNode)"
                        >
                          问AI
                        </v-btn>
                      </div>
                      <v-list density="compact" class="bg-transparent pa-0">
                        <v-list-item
                          v-for="video in selectedNode.relatedVideos"
                          :key="video.id"
                          @click="jumpToVideo(video.id, video.courseId)"
                          class="rounded-lg mb-1"
                          hover
                        >
                          <template v-slot:prepend>
                            <v-icon size="small" color="primary" class="mr-2">mdi-play-circle</v-icon>
                          </template>
                          
                          <v-list-item-title class="text-body-2">{{ video.title }}</v-list-item-title>
                          
                          <v-list-item-subtitle class="mt-1">
                            <div class="d-flex align-center text-caption">
                              <span class="text-primary">{{ video.courseName }}</span>
                              <v-icon size="12" class="mx-1">mdi-circle-small</v-icon>
                              <span class="mr-2">
                                <v-icon size="12" class="mr-1">mdi-eye-outline</v-icon>
                                {{ video.viewCount }}
                              </span>
                              <span>
                                <v-icon size="12" class="mr-1">mdi-clock-outline</v-icon>
                                {{ formatDuration(video.duration) }}
                              </span>
                            </div>
                          </v-list-item-subtitle>
                        </v-list-item>
                      </v-list>
                    </div>
                    
                    <!-- 前置知识点 -->
                    <v-chip-group v-if="selectedNode.prerequisites?.length" class="mb-0">
                      <v-chip
                        v-for="prereq in selectedNode.prerequisites"
                        :key="prereq"
                        size="small"
                        color="#6f23d1"
                        variant="outlined"
                      >
                        {{ prereq }}
                      </v-chip>
                    </v-chip-group>
                  </v-card-text>
                </v-card>
              </v-slide-x-transition>
            </div>
          </v-fade-transition>
        </v-overlay>
        
        <!-- 标签页切换 -->
        <v-card class="rounded-lg">
          <v-tabs
            v-model="currentTab"
            color="#6f23d1"
            align-tabs="center"
            class="px-4"
            slider-color="#6f23d1"
            height="56"
          >
            <v-tab value="knowledge" class="text-subtitle-1">
              <v-icon start>mdi-graph</v-icon>
              课程知识图谱
            </v-tab>
            <v-tab value="path" class="text-subtitle-1">
              <v-icon start>mdi-map-marker-path</v-icon>
              学习路径
            </v-tab>
            <v-tab value="skills" class="text-subtitle-1">
              <v-icon start>mdi-chart-bubble</v-icon>
              能力图谱
            </v-tab>
          </v-tabs>

          <v-divider></v-divider>

          <v-card-text class="pa-6">
            <v-window v-model="currentTab">
              <!-- 课程知识图谱 -->
              <v-window-item value="knowledge">
                <v-row>
                  <v-col cols="12" md="3">
                    <v-select
                      v-model="selectedCourse"
                      :items="courseOptions"
                      item-title="name"
                      item-value="id"
                      label="选择课程"
                      variant="outlined"
                      density="comfortable"
                      hide-details
                      class="rounded-lg"
                    >
                      <template v-slot:prepend>
                        <v-icon color="#6f23d1">mdi-book-open-variant</v-icon>
                      </template>
                    </v-select>
                  </v-col>
                  
                  <v-col cols="12" md="4">
                    <v-text-field
                      v-model="nodeFilter"
                      placeholder="搜索节点..."
                      variant="outlined"
                      density="comfortable"
                      hide-details
                      prepend-inner-icon="mdi-magnify"
                      clearable
                    />
                  </v-col>
                  
                  <v-col cols="12" md="3">
                    <v-btn
                      v-if="selectedCourse && selectedCourse !== 'platform'"
                      color="#6f23d1"
                      variant="outlined"
                      @click="viewPlatformGraph"
                      prepend-icon="mdi-sitemap"
                      block
                    >
                      查看平台知识图谱
                    </v-btn>
                    <v-btn
                      v-else-if="selectedCourse === 'platform'"
                      color="#6f23d1"
                      variant="outlined"
                      @click="backToCourseGraph"
                      prepend-icon="mdi-arrow-left"
                      block
                    >
                      返回课程图谱
                    </v-btn>
                  </v-col>
                  
                  <v-col cols="12" md="2">
                    <v-btn
                      color="primary"
                      variant="outlined"
                      @click="enterImmersiveMode"
                      prepend-icon="mdi-fullscreen"
                      block
                    >
                      沉浸模式
                    </v-btn>
                  </v-col>
                </v-row>

                <!-- 图例和控制面板 -->
                <v-row class="mt-4">
                  <v-col cols="12">
                    <v-card variant="outlined" class="legend-panel">
                      <v-card-text class="py-3">
                        <v-row>
                          <!-- 节点类型图例 -->
                          <v-col cols="12" md="6">
                            <div class="legend-section">
                              <h4 class="text-subtitle-2 mb-2">
                                <v-icon class="mr-1" size="18">mdi-circle</v-icon>
                                节点类型
                              </h4>
                              <div class="d-flex flex-wrap gap-2">
                                <v-chip
                                  v-for="category in nodeCategories"
                                  :key="category.index"
                                  :color="category.color"
                                  size="small"
                                  variant="flat"
                                  class="legend-chip"
                                >
                                  <div 
                                    class="legend-node-dot"
                                    :style="{ backgroundColor: category.color }"
                                  ></div>
                                  {{ category.name }}
                                </v-chip>
                              </div>
                            </div>
                          </v-col>
                          
                          <!-- 关系类型图例 -->
                          <v-col cols="12" md="6">
                            <div class="legend-section">
                              <h4 class="text-subtitle-2 mb-2">
                                <v-icon class="mr-1" size="18">mdi-arrow-right</v-icon>
                                关系类型
                              </h4>
                              <div class="d-flex flex-wrap gap-2">
                                <v-chip
                                  v-for="relation in relationTypes"
                                  :key="relation.type"
                                  :color="relation.color"
                                  size="small"
                                  variant="outlined"
                                  class="legend-chip"
                                >
                                  <div 
                                    class="relation-line-sample" 
                                    :style="{ 
                                      borderColor: relation.color,
                                      borderStyle: relation.lineStyle || 'solid'
                                    }"
                                  ></div>
                                  {{ relation.name }}
                                </v-chip>
                              </div>
                            </div>
                          </v-col>
                        </v-row>
                      </v-card-text>
                    </v-card>
                  </v-col>
                </v-row>

                <!-- 知识图谱容器 -->
                <div class="mt-4" style="position: relative;">
                  <!-- 加载状态 -->
                  <div v-if="loading.knowledge" class="loading-overlay">
                    <div class="text-center">
                      <v-progress-circular indeterminate color="#6f23d1" size="64"></v-progress-circular>
                      <p class="text-subtitle-1 mt-4">正在加载知识图谱...</p>
                    </div>
                  </div>
                  
                  <!-- 空状态 -->
                  <div v-if="!selectedCourse && !loading.knowledge" class="empty-state">
                    <div class="text-center">
                      <v-icon size="64" color="grey">mdi-graph-outline</v-icon>
                      <p class="text-subtitle-1 mt-4 text-medium-emphasis">请选择课程查看知识图谱</p>
                    </div>
                  </div>

                  <!-- 知识图谱容器 -->
                  <div 
                    id="knowledge-graph-container" 
                    class="graph-container"
                    :class="{ 'filtered': nodeFilter }"
                  ></div>
                </div>

                <!-- 知识点详情 -->
                <v-expand-transition>
                  <v-card v-if="selectedNode" class="mt-4" variant="outlined">
                    <v-card-title class="text-h6 pa-4">
                      {{ selectedNode.name }}
                      <v-chip
                        :color="getNodeTypeColor(selectedNode.category || 0)"
                        size="small"
                        class="ml-2"
                      >
                        {{ getNodeTypeName(selectedNode.category || 0) }}
                      </v-chip>
                    </v-card-title>
                    <v-card-text class="pt-2">
                      <p class="text-body-1">{{ selectedNode.description || '暂无描述' }}</p>
                      
                      <!-- 节点特点 -->
                      <div v-if="selectedNode && nodeFeatures.length > 0" class="mt-4">
                        <div class="d-flex align-center mb-2">
                          <v-icon color="primary" class="mr-2">mdi-star-outline</v-icon>
                          <span class="text-subtitle-2 font-weight-medium">知识点关系</span>
                        </div>
                        <v-list density="compact" class="bg-transparent pa-0">
                          <v-list-item
                            v-for="(feature, index) in nodeFeatures"
                            :key="index"
                            class="px-0"
                          >
                            <template v-slot:prepend>
                              <v-icon size="small" :color="getRelationConfig(feature.type).color" class="mr-2">
                                mdi-arrow-right-thin
                              </v-icon>
                            </template>
                            <v-list-item-title class="text-body-2">
                              {{ feature.description }}
                            </v-list-item-title>
                          </v-list-item>
                        </v-list>
                      </div>
                      
                      <!-- 边的描述信息 -->
                      <div v-if="selectedEdgeInfo" class="mt-4">
                        <div class="d-flex align-center mb-2">
                          <v-icon color="primary" class="mr-2">mdi-arrow-decision</v-icon>
                          <span class="text-subtitle-2 font-weight-medium">关系描述</span>
                        </div>
                        <v-card variant="outlined" class="pa-3">
                          <div class="d-flex align-center mb-2">
                            <span class="text-body-2">{{ selectedEdgeInfo.source }} → {{ selectedEdgeInfo.target }}</span>
                            <v-chip
                              :color="getRelationConfig(selectedEdgeInfo.relation_type || 'related').color"
                              size="small"
                              class="ml-2"
                            >
                              {{ getRelationConfig(selectedEdgeInfo.relation_type || 'related').name }}
                            </v-chip>
                          </div>
                          <p class="text-body-2 mb-0">{{ selectedEdgeInfo.description || '暂无关系描述' }}</p>
                        </v-card>
                      </div>
                      
                      <!-- 相关视频列表 -->
                      <div v-if="selectedNode.relatedVideos?.length" class="mt-4">
                        <div class="d-flex align-center justify-space-between mb-2">
                          <div class="d-flex align-center">
                            <v-icon color="primary" class="mr-2">mdi-video-outline</v-icon>
                            <span class="text-subtitle-2 font-weight-medium">相关视频</span>
                          </div>
                          <v-btn
                            color="primary"
                            size="small"
                            variant="text"
                            prepend-icon="mdi-robot"
                            @click="askAI(selectedNode)"
                          >
                            问AI
                          </v-btn>
                        </div>
                        <v-list density="compact" class="bg-transparent pa-0">
                          <v-list-item
                            v-for="video in selectedNode.relatedVideos"
                            :key="video.id"
                            @click="jumpToVideo(video.id, video.courseId)"
                            class="rounded-lg mb-1"
                            hover
                          >
                            <template v-slot:prepend>
                              <v-icon size="small" color="primary" class="mr-2">mdi-play-circle</v-icon>
                            </template>
                            
                            <v-list-item-title class="text-body-2">{{ video.title }}</v-list-item-title>
                            
                            <v-list-item-subtitle class="mt-1">
                              <div class="d-flex align-center text-caption">
                                <span class="text-primary">{{ video.courseName }}</span>
                                <v-icon size="12" class="mx-1">mdi-circle-small</v-icon>
                                <span class="mr-2">
                                  <v-icon size="12" class="mr-1">mdi-eye-outline</v-icon>
                                  {{ video.viewCount }}
                                </span>
                                <span>
                                  <v-icon size="12" class="mr-1">mdi-clock-outline</v-icon>
                                  {{ formatDuration(video.duration) }}
                                </span>
                              </div>
                            </v-list-item-subtitle>
                          </v-list-item>
                        </v-list>
                      </div>
                      
                      <!-- 前置知识点 -->
                      <v-chip-group v-if="selectedNode.prerequisites?.length" class="mt-3">
                        <v-chip
                          v-for="prereq in selectedNode.prerequisites"
                          :key="prereq"
                          size="small"
                          color="#6f23d1"
                          variant="outlined"
                        >
                          {{ prereq }}
                        </v-chip>
                      </v-chip-group>
                    </v-card-text>
                  </v-card>
                </v-expand-transition>

                <!-- 帮助信息 -->
                <v-card class="mt-4" variant="outlined" color="info">
                  <v-card-text class="py-3">
                    <div class="d-flex align-center">
                      <v-icon color="info" class="mr-2">mdi-information-outline</v-icon>
                      <span class="text-body-2">
                        如果课程还没有知识图谱，请前往课程管理页面点击"生成知识图谱"按钮进行生成。
                      </span>
                    </div>
                  </v-card-text>
                </v-card>
              </v-window-item>

              <!-- 学习路径 -->
              <v-window-item value="path">
                <div v-if="loading.path" class="d-flex justify-center align-center" style="height: 400px;">
                  <v-progress-circular indeterminate color="#6f23d1"></v-progress-circular>
                </div>
                <div v-else>
                  <v-timeline align="start" direction="vertical" line-color="rgba(111, 35, 209, 0.12)" line-thickness="4" class="mt-4">
                    <v-timeline-item
                      v-for="(step, index) in demoPath"
                      :key="index"
                      :dot-color="getStatusColor(step.status)"
                      size="small"
                      fill-dot
                    >
                      <template v-slot:opposite>
                        <v-chip
                          :color="getStatusColor(step.status)"
                          :text-color="step.status === 'completed' ? 'white' : undefined"
                          size="small"
                          class="px-2"
                        >
                          {{ getStatusText(step.status) }}
                        </v-chip>
                      </template>
                      
                      <v-card variant="outlined" class="rounded-lg">
                        <v-card-title class="text-subtitle-1 font-weight-bold pa-4">
                          {{ step.name }}
                        </v-card-title>
                        <v-card-text class="pb-2">
                          <p>{{ step.description }}</p>
                        </v-card-text>
                        <v-card-actions class="pa-4 pt-0">
                          <v-btn
                            color="#6f23d1"
                            variant="tonal"
                            size="small"
                            prepend-icon="mdi-play-circle"
                          >
                            开始学习
                          </v-btn>
                        </v-card-actions>
                      </v-card>
                    </v-timeline-item>
                  </v-timeline>
                </div>
              </v-window-item>

              <!-- 能力图谱 -->
              <v-window-item value="skills">
                <div id="skills-chart-container" style="width: 100%; height: 400px; margin-top: 20px;"></div>
                
                <!-- 能力列表 -->
                <v-expansion-panels class="mt-6" variant="accordion">
                  <v-expansion-panel
                    v-for="(skill, index) in demoSkills"
                    :key="index"
                    class="mb-2 rounded-lg"
                  >
                    <v-expansion-panel-title class="py-2">
                      <v-row no-gutters align="center">
                        <v-col cols="4" class="text-subtitle-1 font-weight-medium">
                          {{ skill.name }}
                        </v-col>
                        <v-col cols="8">
                          <v-progress-linear
                            :model-value="skill.progress"
                            color="#6f23d1"
                            height="20"
                            rounded
                          >
                            <template v-slot:default="{ value }">
                              <span class="white--text text-caption">Level {{ skill.level }} ({{ Math.ceil(value) }}%)</span>
                            </template>
                          </v-progress-linear>
                        </v-col>
                      </v-row>
                    </v-expansion-panel-title>
                    <v-expansion-panel-text>
                      <v-list v-if="skill.children" class="bg-transparent pa-0">
                        <v-list-item
                          v-for="(subSkill, subIndex) in skill.children"
                          :key="subIndex"
                          :subtitle="'Level ' + subSkill.level"
                          class="px-0"
                        >
                          <template v-slot:default>
                            <v-list-item-title class="mb-2">{{ subSkill.name }}</v-list-item-title>
                            <v-progress-linear
                              :model-value="subSkill.progress"
                              color="#6f23d1"
                              height="6"
                              rounded
                            ></v-progress-linear>
                          </template>
                        </v-list-item>
                      </v-list>
                    </v-expansion-panel-text>
                  </v-expansion-panel>
                </v-expansion-panels>
              </v-window-item>
            </v-window>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- 视频选择对话框 -->
    <v-dialog v-model="showVideoDialog" max-width="500">
      <v-card>
        <v-card-title class="text-h6 pa-4">
          选择要跳转的视频
          <div class="text-caption text-medium-emphasis mt-1">
            以下视频中包含关于"{{ pendingKeyword }}"的内容
          </div>
        </v-card-title>
        <v-card-text class="pt-2">
          <v-radio-group v-model="selectedVideo" density="compact">
            <v-radio
              v-for="video in selectedNode?.relatedVideos"
              :key="video.id"
              :value="video"
              color="primary"
              class="mb-3"
            >
              <template v-slot:label>
                <div class="video-option">
                  <div class="text-subtitle-2 mb-1">{{ video.title }}</div>
                  <div class="text-caption text-medium-emphasis d-flex align-center flex-wrap">
                    <span class="d-flex align-center me-3">
                      <v-icon size="12" class="mr-1">mdi-school</v-icon>
                      {{ video.courseName }}
                    </span>
                    <span class="d-flex align-center me-3">
                      <v-icon size="12" class="mr-1">mdi-eye-outline</v-icon>
                      {{ video.viewCount || 0 }}次观看
                    </span>
                    <span class="d-flex align-center">
                      <v-icon size="12" class="mr-1">mdi-clock-outline</v-icon>
                      {{ formatDuration(video.duration) }}
                    </span>
                  </div>
                </div>
              </template>
            </v-radio>
          </v-radio-group>
        </v-card-text>
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn
            color="grey"
            variant="text"
            @click="showVideoDialog = false"
          >
            取消
          </v-btn>
          <v-btn
            color="primary"
            @click="handleVideoSelect(selectedVideo)"
            :disabled="!selectedVideo"
          >
            确定
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed, nextTick, onBeforeUnmount } from 'vue'
import type { KnowledgeNode, LearningPath, SkillNode, GraphNode } from '../api/knowledgeMapService'
import knowledgeMapService from '../api/knowledgeMapService'
import courseService from '../api/courseService'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { GraphChart, RadarChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent
} from 'echarts/components'

// 类型定义
interface Course {
  id: string
  name: string
}

interface GraphLink {
  source: string
  target: string
  type?: string
  label?: string
  relation_type?: string
  lineStyle?: {
    opacity?: number
    width?: number
  }
  strength?: number
  description?: string
}

// 注册 ECharts 组件
echarts.use([
  CanvasRenderer,
  GraphChart,
  RadarChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent
])

// 状态管理
const currentTab = ref('knowledge')
const selectedCourse = ref('platform')
const selectedNode = ref<GraphNode | null>(null)
const nodeFilter = ref('')
const isImmersiveMode = ref(false)
const loading = ref({
  knowledge: false,
  path: false,
  skills: false
})

// 图表实例
let knowledgeChart: echarts.ECharts | null = null
let immersiveChart: echarts.ECharts | null = null
let skillsChart: echarts.ECharts | null = null

// 课程数据
const courses = ref<Course[]>([])

// 图例配置
const nodeCategories = ref([
  { 
    index: 0, 
    name: '核心概念', 
    color: '#6f23d1',
    icon: 'mdi-star' 
  },
  { 
    index: 1, 
    name: '主要模块', 
    color: '#2196F3',
    icon: 'mdi-puzzle' 
  },
  { 
    index: 2, 
    name: '具体知识点', 
    color: '#4CAF50',
    icon: 'mdi-lightbulb' 
  }
])

const relationTypes = ref([
  { 
    type: 'prerequisite', 
    name: '前置关系', 
    color: '#F44336',
    lineStyle: 'solid'
  },
  { 
    type: 'related', 
    name: '相关关系', 
    color: '#607D8B',
    lineStyle: 'dotted'
  },
  { 
    type: 'contains', 
    name: '包含关系', 
    color: '#2196F3',
    lineStyle: 'solid'
  }
])

// 获取课程列表
const fetchCourses = async () => {
  try {
    const response = await courseService.getCourses()
    if (response.data.code === 200) {
      courses.value = response.data.data.list.map((course: any) => ({
        id: course.id,
        name: course.name
      }))
      
      if (courses.value.length > 0 && !selectedCourse.value) {
        selectedCourse.value = courses.value[0].id
      }
    } else {
      console.error('获取课程列表失败:', response.data.msg)
    }
  } catch (error) {
    console.error('获取课程列表出错:', error)
    // 如果API失败，使用示例数据作为fallback
    courses.value = [
      { id: '1', name: '计算机网络' },
      { id: '2', name: '操作系统' },
      { id: '3', name: '数据结构' }
    ]
  }
}

// 计算属性：课程选项（包含平台图谱选项）
const courseOptions = computed(() => {
  const options = [...courses.value]
  options.unshift({ id: 'platform', name: '平台知识图谱（所有课程）' })
  return options
})

// 沉浸模式控制
const enterImmersiveMode = () => {
  isImmersiveMode.value = true
  nextTick(() => {
    initImmersiveChart()
  })
}

const exitImmersiveMode = () => {
  isImmersiveMode.value = false
  if (immersiveChart) {
    immersiveChart.dispose()
    immersiveChart = null
  }
}

const toggleImmersiveMode = () => {
  if (isImmersiveMode.value) {
    exitImmersiveMode()
  } else {
    enterImmersiveMode()
  }
}

// 查看平台知识图谱
const viewPlatformGraph = () => {
  selectedCourse.value = 'platform'
}

// 返回课程图谱
const backToCourseGraph = () => {
  if (courses.value.length > 0) {
    selectedCourse.value = courses.value[0].id
  }
}

// 获取节点类型颜色
const getNodeTypeColor = (category: number): string => {
  const categoryConfig = nodeCategories.value.find(c => c.index === category)
  return categoryConfig?.color || '#6f23d1'
}

// 获取节点类型名称
const getNodeTypeName = (category: number): string => {
  const categoryConfig = nodeCategories.value.find(c => c.index === category)
  return categoryConfig?.name || '未知类型'
}

// 获取关系类型配置
const getRelationConfig = (type: string) => {
  return relationTypes.value.find(r => r.type === type) || relationTypes.value[0]
}

// 获取课程知识图谱数据
const fetchCourseKnowledgeGraph = async (courseId: string) => {
  if (!courseId || courseId === 'platform') return
  
  loading.value.knowledge = true
  try {
    const response = await knowledgeMapService.getCourseKnowledgeGraph(courseId)
    if (response.data.code === 200) {
      const graphData = response.data.data
      if (graphData && graphData.nodes && graphData.links && graphData.nodes.length > 0) {
        actualGraphData.value = graphData
        nextTick(() => {
          initKnowledgeChart()
        })
      } else {
        console.warn('课程知识图谱数据为空，使用示例数据')
        actualGraphData.value = null
        nextTick(() => {
          initKnowledgeChart()
        })
      }
    } else {
      throw new Error(response.data.msg || '获取课程知识图谱失败')
    }
  } catch (error: any) {
    console.error('获取课程知识图谱失败:', error)
    // 如果API失败，使用示例数据作为fallback
    actualGraphData.value = null
    nextTick(() => {
      initKnowledgeChart()
    })
  } finally {
    loading.value.knowledge = false
  }
}

// 获取平台知识图谱数据
const fetchPlatformKnowledgeGraph = async () => {
  loading.value.knowledge = true
  try {
    const response = await knowledgeMapService.getPlatformKnowledgeGraph()
    if (response.data.code === 200) {
      const graphData = response.data.data
      if (graphData && graphData.nodes && graphData.links && graphData.nodes.length > 0) {
        actualGraphData.value = graphData
        nextTick(() => {
          initKnowledgeChart()
        })
      } else {
        console.warn('平台知识图谱数据为空，使用示例数据')
        actualGraphData.value = null
        nextTick(() => {
          initKnowledgeChart()
        })
      }
    } else {
      throw new Error(response.data.msg || '获取平台知识图谱失败')
    }
  } catch (error: any) {
    console.error('获取平台知识图谱失败:', error)
    // 如果API失败，使用示例数据作为fallback
    actualGraphData.value = null
    nextTick(() => {
      initKnowledgeChart()
    })
  } finally {
    loading.value.knowledge = false
  }
}

// 示例数据（作为fallback）
const sampleGraphData = {
  nodes: [
    { id: '1', name: '计算机网络', symbolSize: 60, category: 0, description: '计算机网络的基础概念和原理' },
    { id: '2', name: 'TCP/IP协议', symbolSize: 50, category: 1, description: 'TCP/IP协议栈详解' },
    { id: '3', name: '网络安全', symbolSize: 50, category: 1, description: '网络安全基础知识' },
    { id: '4', name: 'HTTP协议', symbolSize: 45, category: 2, description: 'HTTP协议详解' },
    { id: '5', name: 'TCP协议', symbolSize: 45, category: 2, description: 'TCP协议机制' },
    { id: '6', name: 'IP协议', symbolSize: 45, category: 2, description: 'IP协议原理' },
    { id: '7', name: '加密算法', symbolSize: 45, category: 2, description: '常用加密算法' },
    { id: '8', name: '防火墙', symbolSize: 45, category: 3, description: '防火墙技术与应用' },
    { id: '9', name: 'SSL/TLS', symbolSize: 40, category: 2, description: 'SSL/TLS安全协议' },
    { id: '10', name: '网络编程', symbolSize: 40, category: 3, description: 'Socket网络编程' }
  ],
  links: [
    { source: '1', target: '2', type: 'prerequisite' },
    { source: '1', target: '3', type: 'prerequisite' },
    { source: '2', target: '4', type: 'dependency' },
    { source: '2', target: '5', type: 'composition' },
    { source: '2', target: '6', type: 'composition' },
    { source: '3', target: '7', type: 'dependency' },
    { source: '3', target: '8', type: 'association' },
    { source: '7', target: '9', type: 'prerequisite' },
    { source: '2', target: '10', type: 'prerequisite' },
    { source: '4', target: '9', type: 'association' }
  ]
}

// 实际的图谱数据
const actualGraphData = ref<any>(null)

// 示例学习路径数据
const demoPath = [
  { 
    id: '1',
    name: '计算机网络基础',
    description: '学习计算机网络的基本概念和原理，理解网络通信的基础知识。',
    status: 'completed',
    order: 1
  },
  {
    id: '2',
    name: 'TCP/IP协议族',
    description: '深入学习TCP/IP协议栈的各层协议，掌握网络通信的核心技术。',
    status: 'in-progress',
    order: 2
  },
  {
    id: '3',
    name: '网络安全技术',
    description: '学习网络安全基础，包括加密算法、防火墙技术和网络攻防。',
    status: 'not-started',
    order: 3
  },
  {
    id: '4',
    name: '网络编程实践',
    description: '通过实践项目，掌握Socket编程和网络应用开发技术。',
    status: 'not-started',
    order: 4
  }
]

// 示例技能数据
const demoSkills = [
  {
    id: '1',
    name: '计算机网络',
    level: 3,
    progress: 75,
    children: [
      { id: '1-1', name: '网络协议', level: 4, progress: 80 },
      { id: '1-2', name: '网络安全', level: 3, progress: 60 },
      { id: '1-3', name: '网络编程', level: 2, progress: 50 }
    ]
  },
  {
    id: '2',
    name: '操作系统',
    level: 2,
    progress: 45,
    children: [
      { id: '2-1', name: '进程管理', level: 2, progress: 45 },
      { id: '2-2', name: '内存管理', level: 2, progress: 40 },
      { id: '2-3', name: '文件系统', level: 3, progress: 65 }
    ]
  },
  {
    id: '3',
    name: '算法与数据结构',
    level: 4,
    progress: 85,
    children: [
      { id: '3-1', name: '基础算法', level: 5, progress: 90 },
      { id: '3-2', name: '数据结构', level: 4, progress: 85 },
      { id: '3-3', name: '高级算法', level: 3, progress: 70 }
    ]
  }
]

// 节点筛选功能
const filteredGraphData = computed(() => {
  // 使用真实数据或示例数据
  const sourceData = actualGraphData.value || sampleGraphData
  
  if (!nodeFilter.value || nodeFilter.value.trim() === '') {
    return sourceData
  }

  const searchTerm = nodeFilter.value.toLowerCase().trim()
  
  // 找到匹配的节点
  const matchedNodes = sourceData.nodes.filter((node: any) => 
    node.name.toLowerCase().includes(searchTerm)
  )
  
  if (matchedNodes.length === 0) {
    return { nodes: [], links: [] }
  }

  // 获取匹配节点的ID集合
  const matchedNodeIds = new Set(matchedNodes.map((node: any) => node.id))
  
  // 找到所有与匹配节点相关的节点（关联节点）
  const relatedNodeIds = new Set(matchedNodeIds)
  
  sourceData.links.forEach((link: any) => {
    if (matchedNodeIds.has(link.source)) {
      relatedNodeIds.add(link.target)
    }
    if (matchedNodeIds.has(link.target)) {
      relatedNodeIds.add(link.source)
    }
  })
  
  // 筛选节点和链接
  const filteredNodes = sourceData.nodes.filter((node: any) => 
    relatedNodeIds.has(node.id)
  )
  
  const filteredLinks = sourceData.links.filter((link: any) => 
    relatedNodeIds.has(link.source) && relatedNodeIds.has(link.target)
  )
  
  return {
    nodes: filteredNodes,
    links: filteredLinks
  }
})

// 获取图表配置
const getChartOption = (data: any) => {
  return {
    title: {
      text: selectedCourse.value === 'platform' ? '平台知识图谱' : '课程知识图谱',
      left: 'center',
      top: 20,
      textStyle: {
        fontSize: 16,
        fontWeight: 'bold',
        color: '#6f23d1'
      }
    },
    tooltip: {
      trigger: 'item',
      formatter: function(params: any) {
        if (params.dataType === 'node') {
          const node = params.data
          return `
            <div style="padding: 10px;">
              <strong>${node.name}</strong><br/>
              <span style="color: ${getNodeTypeColor(node.category)};">
                ${getNodeTypeName(node.category)}
              </span><br/>
              ${node.description || '暂无描述'}
            </div>
          `
        } else if (params.dataType === 'edge') {
          const link = params.data
          const relationConfig = getRelationConfig(link.relation_type || 'association')
          return `
            <div style="padding: 10px;">
              <strong>关系类型：</strong>${relationConfig.name}<br/>
              <strong>源节点：</strong>${link.source}<br/>
              <strong>目标节点：</strong>${link.target}
            </div>
          `
        }
        return ''
      }
    },
    legend: [{
      data: nodeCategories.value.map(cat => cat.name),
      orient: 'horizontal',
      left: 'center',
      bottom: 20,
      textStyle: {
        fontSize: 12
      }    }],
    animationDurationUpdate: 1500,
    animationEasingUpdate: 'quintInOut' as any,
    series: [{
      type: 'graph',
      layout: 'force',
      data: data.nodes.map((node: GraphNode) => ({
        ...node,
        itemStyle: {
          color: getNodeTypeColor(node.category)
        },
        label: {
          show: true,
          position: 'bottom',
          fontSize: 12,
          fontWeight: 'bold'
        }
      })),
      links: data.links.map((link: GraphLink) => {
        const relationConfig = getRelationConfig(link.relation_type || 'association')
        return {
          ...link,
          lineStyle: {
            color: relationConfig.color,
            width: 2,
            type: relationConfig.lineStyle === 'dashed' ? 'dashed' : 
                  relationConfig.lineStyle === 'dotted' ? 'dotted' : 'solid'
          },
          label: {
            show: false
          }
        }
      }),
      categories: nodeCategories.value.map(cat => ({
        name: cat.name,
        itemStyle: {
          color: cat.color
        }
      })),
      roam: true,
      focusNodeAdjacency: true,
      itemStyle: {
        borderColor: '#fff',
        borderWidth: 1,
        shadowBlur: 10,
        shadowColor: 'rgba(0, 0, 0, 0.3)'
      },
      label: {
        position: 'bottom',
        formatter: '{b}'
      },
      lineStyle: {
        color: 'source',
        curveness: 0.3
      },
      emphasis: {
        focus: 'adjacency',
        lineStyle: {
          width: 4
        }
      },
      force: {
        repulsion: 2000,
        gravity: 0.1,
        edgeLength: [50, 200],
        layoutAnimation: true
      }
    }]
  }
}

// 修改图表初始化中的事件绑定
const initChartEvents = (chart: echarts.ECharts) => {
  chart.on('click', function(params: any) {
    if (params.dataType === 'node') {
      handleNodeSelect(params.data)
    } else if (params.dataType === 'edge') {
      handleEdgeSelect(params.data)
    }
  })
}

// 修改初始化函数
const initKnowledgeChart = async () => {
  await nextTick()
  
  const chartDom = document.getElementById('knowledge-graph-container')
  if (!chartDom) {
    console.warn('知识图谱容器元素不存在')
    return
  }
  
  // 设置容器样式
  chartDom.style.width = '100%'
  chartDom.style.height = '600px'
  chartDom.style.display = 'block'
  
  // 释放之前的实例
  if (knowledgeChart) {
    knowledgeChart.dispose()
  }
  
  // 初始化ECharts实例
  knowledgeChart = echarts.init(chartDom)
  
  // 设置图表配置
  const option = getChartOption(filteredGraphData.value)
  knowledgeChart.setOption(option, true)
  
  initChartEvents(knowledgeChart)  // 添加事件监听
  
  // 设置图表resize监听
  const resizeHandler = () => {
    if (knowledgeChart) {
      knowledgeChart.resize()
    }
  }
  
  window.addEventListener('resize', resizeHandler)
  
  // 清理函数
  onBeforeUnmount(() => {
    window.removeEventListener('resize', resizeHandler)
  })
}

// 初始化沉浸模式图谱
const initImmersiveChart = async () => {
  await nextTick()
  
  const chartDom = document.getElementById('immersive-graph-container')
  if (!chartDom) {
    console.warn('沉浸模式图谱容器元素不存在')
    return
  }
  
  // 释放之前的实例
  if (immersiveChart) {
    immersiveChart.dispose()
  }
  
  // 初始化ECharts实例
  immersiveChart = echarts.init(chartDom)
  
  // 设置图表配置（沉浸模式下的特殊配置）
  const option = {
    ...getChartOption(filteredGraphData.value),
    backgroundColor: 'transparent',
    title: {
      ...getChartOption(filteredGraphData.value).title,
      textStyle: {
        fontSize: 20,
        fontWeight: 'bold',
        color: '#ffffff'
      }
    },
    legend: [{
      ...getChartOption(filteredGraphData.value).legend[0],
      textStyle: {
        fontSize: 14,
        color: '#ffffff'
      }
    }]
  }
  
  immersiveChart.setOption(option, true)
  
  initChartEvents(immersiveChart)  // 添加事件监听
  
  // 设置图表resize监听
  const resizeHandler = () => {
    if (immersiveChart) {
      immersiveChart.resize()
    }
  }
  
  window.addEventListener('resize', resizeHandler)
}

// 初始化能力雷达图
const initSkillsChart = async () => {
  await nextTick()
  
  const chartDom = document.getElementById('skills-chart-container')
  if (!chartDom) return
  
  if (skillsChart) {
    skillsChart.dispose()
  }
  
  skillsChart = echarts.init(chartDom)
  
  const option = {
    title: {
      text: '能力雷达图',
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 'bold',
        color: '#6f23d1'
      }
    },
    tooltip: {
      trigger: 'item'
    },
    radar: {
      indicator: demoSkills.map(skill => ({
        name: skill.name,
        max: 100
      })),
      radius: '65%',
      center: ['50%', '55%']
    },
    series: [{
      type: 'radar',
      data: [{
        value: demoSkills.map(skill => skill.progress),
        name: '当前能力',
        itemStyle: {
          color: '#6f23d1'
        },
        areaStyle: {
          color: 'rgba(111, 35, 209, 0.2)'
        }
      }]
    }]
  }
  
  skillsChart.setOption(option)
}

// 状态文本获取函数
const getStatusText = (status: string) => {
  switch (status) {
    case 'completed': return '已完成'
    case 'in-progress': return '进行中'
    case 'not-started': return '未开始'
    default: return '未知'
  }
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'completed': return 'success'
    case 'in-progress': return 'warning'
    case 'not-started': return 'grey'
    default: return 'grey'
  }
}

// 监听器
watch(nodeFilter, () => {
  if (knowledgeChart) {
    const option = getChartOption(filteredGraphData.value)
    knowledgeChart.setOption(option, true)
  }
  if (immersiveChart) {
    const option = {
      ...getChartOption(filteredGraphData.value),
      backgroundColor: 'transparent',
      title: {
        ...getChartOption(filteredGraphData.value).title,
        textStyle: {
          fontSize: 20,
          fontWeight: 'bold',
          color: '#ffffff'
        }
      },
      legend: [{
        ...getChartOption(filteredGraphData.value).legend[0],
        textStyle: {
          fontSize: 14,
          color: '#ffffff'
        }
      }]
    }
    immersiveChart.setOption(option, true)
  }
})

watch(selectedCourse, async (newValue) => {
  if (newValue) {
    if (newValue === 'platform') {
      // 获取平台知识图谱
      await fetchPlatformKnowledgeGraph()
    } else {
      // 获取特定课程的知识图谱
      await fetchCourseKnowledgeGraph(newValue)
    }
  } else {
    // 没有选择课程时清空数据
    actualGraphData.value = null
    loading.value.knowledge = false
  }
})

watch(currentTab, (newTab) => {
  if (newTab === 'knowledge') {
    nextTick(() => {
      initKnowledgeChart()
    })
  } else if (newTab === 'skills') {
    nextTick(() => {
      initSkillsChart()
    })
  }
})

// 生命周期
onMounted(async () => {
  await fetchCourses()
  
  // 初始化当前标签页对应的图表
  if (currentTab.value === 'knowledge') {
    // 根据默认选择的课程加载知识图谱数据
    if (selectedCourse.value === 'platform') {
      await fetchPlatformKnowledgeGraph()
    } else if (selectedCourse.value) {
      await fetchCourseKnowledgeGraph(selectedCourse.value)
    } else {
      // 如果没有选择课程，显示空状态
      loading.value.knowledge = false
      nextTick(() => {
        initKnowledgeChart()
      })
    }
  } else if (currentTab.value === 'skills') {
    initSkillsChart()
  }
})

onBeforeUnmount(() => {
  if (knowledgeChart) {
    knowledgeChart.dispose()
  }
  if (immersiveChart) {
    immersiveChart.dispose()
  }
  if (skillsChart) {
    skillsChart.dispose()
  }
})

const router = useRouter()  // 获取路由实例

// 跳转到视频页面
const jumpToVideo = (videoId: string, courseId: string) => {
  router.push(`/course/${courseId}/video/${videoId}`)
}

// 获取关键词相关视频
const fetchKeywordVideos = async (keywordId: string) => {
  try {
    const response = await knowledgeMapService.getKeywordRelatedVideos(keywordId)
    if (response.data.code === 200) {
      const keywordData = response.data.data
      if (selectedNode.value) {
        selectedNode.value = {
          ...selectedNode.value,
          relatedVideos: keywordData.videos.map((video: any) => ({
            id: video.id,
            title: video.title,
            courseName: video.course.name,
            courseId: video.course.id,
            viewCount: video.view_count,
            duration: video.duration
          }))
        }
      }
    }
  } catch (error) {
    console.error('获取关键词相关视频失败:', error)
    if (selectedNode.value) {
      selectedNode.value.relatedVideos = []
    }
  }
}

// 添加 selectedEdgeInfo 状态
const selectedEdgeInfo = ref<GraphLink | null>(null)

// 修改图表点击事件处理
const handleNodeSelect = async (node: any) => {
  // 如果点击的是当前选中的节点，则取消选中
  if (selectedNode.value && selectedNode.value.id === node.id) {
    selectedNode.value = null
    return
  }
  
  selectedNode.value = node
  selectedEdgeInfo.value = null  // 清空边的信息
  if (node && node.id) {
    await fetchKeywordVideos(node.id)
  }
}

// 添加边的点击事件处理
const handleEdgeSelect = (edge: any) => {
  selectedEdgeInfo.value = edge
  selectedNode.value = null  // 清空节点信息
}

// 添加时间格式化函数
const formatDuration = (seconds: number): string => {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const remainingSeconds = Math.floor(seconds % 60)
  
  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`
  }
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
}

// 添加计算属性：节点特点
const nodeFeatures = computed(() => {
  if (!selectedNode.value || !actualGraphData.value) return []
  
  const features: Array<{ type: string; description: string }> = []
  
  // 遍历所有边
  actualGraphData.value.links.forEach((link: GraphLink) => {
    // 如果当前节点是源节点或目标节点
    if (link.source === selectedNode.value?.id || link.target === selectedNode.value?.id) {
      // 确保有描述
      if (link.description) {
        features.push({
          type: link.relation_type || 'related',
          description: link.description
        })
      }
    }
  })
  
  return features
})

// 在script部分添加视频选择对话框相关的状态
const showVideoDialog = ref(false)
const selectedVideo = ref<any>(null)
const pendingKeyword = ref<any>(null)

// 修改askAI函数
const askAI = (node: any) => {
  if (!node || !node.relatedVideos?.length) return
  
  // 如果只有一个相关视频，直接跳转
  if (node.relatedVideos.length === 1) {
    const video = node.relatedVideos[0]
    router.push({
      path: `/course/${video.courseId}/video/${video.id}`,
      query: {
        askAI: 'true',
        keyword: node.name
      }
    })
  } else {
    // 如果有多个相关视频，显示选择对话框
    pendingKeyword.value = node.name
    showVideoDialog.value = true
  }
}

// 添加处理视频选择的函数
const handleVideoSelect = (video: any) => {
  showVideoDialog.value = false
  if (video && pendingKeyword.value) {
    router.push({
      path: `/course/${video.courseId}/video/${video.id}`,
      query: {
        askAI: 'true',
        keyword: pendingKeyword.value
      }
    })
  }
  // 清空状态
  selectedVideo.value = null
  pendingKeyword.value = null
}
</script>

<style scoped>
.knowledge-map-container {
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  min-height: 100vh;
}

.graph-container {
  width: 100%;
  height: 600px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background: white;
  position: relative;
  overflow: hidden;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

.empty-state {
  height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.legend-panel {
  border: 1px solid #e0e0e0;
}

.legend-section h4 {
  color: #6f23d1;
}

.legend-chip {
  margin: 2px !important;
}

.legend-node-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  margin-right: 6px;
  display: inline-block;
}

.relation-line-sample {
  width: 20px;
  height: 0;
  border-top: 2px solid;
  margin-right: 6px;
  display: inline-block;
}

/* 沉浸模式样式 */
.immersive-overlay {
  background: rgba(0, 0, 0, 0.95) !important;
}

.immersive-container {
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.immersive-header {
  height: 80px;
  background: rgba(111, 35, 209, 0.9);
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  backdrop-filter: blur(10px);
}

.immersive-graph {
  flex: 1;
  background: transparent;
}

/* 沉浸模式详情卡片样式 */
.immersive-detail-card {
  position: fixed;
  top: 100px;
  right: 24px;
  width: 380px;
  max-height: calc(100vh - 140px);
  overflow-y: auto;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  z-index: 10000;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.immersive-detail-card::-webkit-scrollbar {
  width: 6px;
}

.immersive-detail-card::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 3px;
}

.immersive-detail-card::-webkit-scrollbar-thumb {
  background: rgba(111, 35, 209, 0.6);
  border-radius: 3px;
}

.immersive-detail-card::-webkit-scrollbar-thumb:hover {
  background: rgba(111, 35, 209, 0.8);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .legend-chip {
    margin-bottom: 4px !important;
  }
  
  .immersive-header {
    flex-direction: column;
    height: auto;
    padding: 16px;
    gap: 16px;
  }
  
  /* 移动端沉浸模式详情卡片调整 */
  .immersive-detail-card {
    position: fixed;
    top: 120px;
    left: 16px;
    right: 16px;
    width: auto;
    max-height: calc(100vh - 160px);
  }
}

@media (max-width: 480px) {
  .immersive-detail-card {
    top: 140px;
    left: 8px;
    right: 8px;
    max-height: calc(100vh - 180px);
  }
}

/* 动画效果 */
.v-fade-transition-enter-active {
  transition: all 0.3s ease-out;
}

.v-fade-transition-leave-active {
  transition: all 0.3s ease-in;
}

.v-fade-transition-enter-from {
  opacity: 0;
  transform: scale(0.95);
}

.v-fade-transition-leave-to {
  opacity: 0;
  transform: scale(1.05);
}

/* 筛选状态样式 */
.graph-container.filtered {
  border-color: #6f23d1;
  box-shadow: 0 0 0 2px rgba(111, 35, 209, 0.2);
}

/* 视频选择对话框样式 */
.video-option {
  padding: 8px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.video-option:hover {
  background-color: rgba(0, 0, 0, 0.03);
}
</style>