import request from './index'

export interface KnowledgeNode {
  id: string;
  name: string;
  type: string;
  description?: string;
  prerequisites?: string[];
  children?: KnowledgeNode[];
}

export interface GraphNode {
  id: string;
  name: string;
  symbolSize: number;
  category: number;
  description?: string;
  prerequisites?: string[];
  course_count?: number;
  video_count?: number;
  relatedVideos?: Array<{
    id: string;
    title: string;
    courseName: string;
    courseId: string;
    viewCount: number;
    duration: number;
  }>;
}

export interface LearningPath {
  id: string;
  name: string;
  description: string;
  steps: {
    id: string;
    name: string;
    courseId?: string;
    status: 'completed' | 'in-progress' | 'not-started';
    order: number;
  }[];
}

export interface SkillNode {
  id: string;
  name: string;
  level: number;
  progress: number;
  children?: SkillNode[];
}

const knowledgeMapService = {
  // 获取课程知识图谱
  getKnowledgeMap: (courseId: string) => {
    return request({
      url: `/api/knowledge-map/${courseId}`,
      method: 'get'
    })
  },

  // 获取推荐学习路径
  getLearningPath: (userId: string) => {
    return request({
      url: `/api/learning-path/${userId}`,
      method: 'get'
    })
  },

  // 获取个人能力图谱
  getSkillMap: (userId: string) => {
    return request({
      url: `/api/skill-map/${userId}`,
      method: 'get'
    })
  },

  // 更新学习进度
  updateLearningProgress: (data: { userId: string; nodeId: string; completed: boolean }) => {
    return request({
      url: '/api/learning-progress',
      method: 'post',
      data
    })
  },  // 生成知识图谱
  generateKnowledgeGraph: (data: { courseId: string; forceRegenerate?: boolean; incremental?: boolean }) => {
    return request({
      url: '/api/knowledge-graph/generate',
      method: 'post',
      data
    })
  },

  // 获取课程知识图谱数据
  getCourseKnowledgeGraph: (courseId: string) => {
    return request({
      url: `/api/knowledge-graph/course/${courseId}`,
      method: 'get'
    })
  },

  // 获取平台知识图谱数据
  getPlatformKnowledgeGraph: () => {
    return request({
      url: '/api/knowledge-graph/platform',
      method: 'get'
    })
  },

  // 获取关键词相关视频
  getKeywordVideos: (keywordId: string) => {
    return request({
      url: `/api/knowledge-graph/keyword/${keywordId}/videos`,
      method: 'get'
    })
  },

  // 获取知识图谱生成任务状态
  getTaskStatus: (taskId: string) => {
    return request({
      url: `/api/knowledge-graph/task/${taskId}`,
      method: 'get'
    })
  },

  // 获取关键词相关视频
  getKeywordRelatedVideos: (keywordId: string) => {
    return request({
      url: `/api/knowledge-graph/keyword/${keywordId}/videos`,
      method: 'get'
    })
  },

  // 获取课程视频处理状态
  getCourseVideosProcessingStatus: (courseId: string) => {
    return request({
      url: `/api/knowledge-graph/course/${courseId}/videos-status`,
      method: 'get'
    })
  }
}

export default knowledgeMapService