/**
 * 图片路径处理工具
 */

const API_BASE_URL = 'http://localhost:5000';

/**
 * 处理图片URL，将相对路径转换为完整URL
 * @param imagePath 图片路径
 * @param fallbackUrl 默认图片URL
 * @returns 处理后的完整图片URL
 */
export function processImageUrl(imagePath: string | null | undefined, fallbackUrl?: string): string {
  // 如果没有图片路径，使用默认图片或随机图片
  if (!imagePath) {
    return fallbackUrl || 'https://picsum.photos/400/225?random=' + Math.random();
  }
  
  // 如果已经是完整URL，直接返回
  if (imagePath.startsWith('http://') || imagePath.startsWith('https://')) {
    return imagePath;
  }
  
  // 如果是相对路径（以/temp_img/开头），转换为完整URL
  if (imagePath.startsWith('/temp_img/') || 
      imagePath.startsWith('/temp_video/') || 
      imagePath.startsWith('/temp_docs/') || 
      imagePath.startsWith('/temp_avatars/')) {
    return `${API_BASE_URL}${imagePath}`;
  }
  
  // 如果是其他形式的相对路径，也尝试拼接
  if (imagePath.startsWith('/')) {
    return `${API_BASE_URL}${imagePath}`;
  }
  
  // 其他情况，假设是文件名，拼接到temp_img目录
  return `${API_BASE_URL}/temp_img/${imagePath}`;
}

/**
 * 处理课程封面图片URL
 * @param courseId 课程ID
 * @param imagePath 课程图片路径
 * @returns 处理后的图片URL
 */
export function processCourseImageUrl(courseId: string, imagePath: string | null | undefined): string {
  const fallbackUrl = `https://picsum.photos/400/225?random=${courseId}`;
  return processImageUrl(imagePath, fallbackUrl);
}

/**
 * 处理用户头像URL
 * @param userId 用户ID
 * @param avatarPath 头像路径
 * @returns 处理后的头像URL
 */
export function processAvatarUrl(userId: string, avatarPath: string | null | undefined): string {
  const fallbackUrl = `https://api.dicebear.com/7.x/avataaars/svg?seed=${userId}`;
  return processImageUrl(avatarPath, fallbackUrl);
} 