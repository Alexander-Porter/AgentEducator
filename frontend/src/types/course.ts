export interface Course {
  id: string;
  thumbnail: string;
  title: string;
  duration: string;
  students: number;
  teacher: string;
  category: string;
  description?: string;
}