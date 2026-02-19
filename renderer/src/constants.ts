import { Avatar, Voice, Project } from './types';

export const MOCK_AVATARS: Avatar[] = [
  { id: '1', name: '安娜 (新闻)', thumbnail: 'https://picsum.photos/id/64/300/500', category: 'official', tags: ['专业', '女主播'] },
  { id: '2', name: '李明 (商务)', thumbnail: 'https://picsum.photos/id/91/300/500', category: 'official', tags: ['职场', '男主播'] },
  { id: '3', name: '小美 (亲和)', thumbnail: 'https://picsum.photos/id/338/300/500', category: 'official', tags: ['亲和', '女主播'] },
  { id: '4', name: 'Jason (English)', thumbnail: 'https://picsum.photos/id/177/300/500', category: 'official', tags: ['外语', '男主播'] },
  { id: '5', name: '自定义主播-01', thumbnail: 'https://picsum.photos/id/342/300/500', category: 'custom', tags: ['自定义'] },
];

export const MOCK_VOICES: Voice[] = [
  { id: 'v1', name: '云希', gender: 'male', style: '沉稳', isDownloaded: true },
  { id: 'v2', name: '晓晓', gender: 'female', style: '活泼', isDownloaded: true },
  { id: 'v3', name: '云野', gender: 'male', style: '讲故事', isDownloaded: false },
  { id: 'v4', name: '陕西话-老李', gender: 'male', style: '方言', isDownloaded: false },
];

export const MOCK_PROJECTS: Project[] = [
  { id: 'p1', title: '产品介绍_V1.mp4', thumbnail: 'https://picsum.photos/id/1/400/225', duration: '00:45', createdAt: '2023-10-24 10:30', status: 'completed' },
  { id: 'p2', title: '口播文案_草稿', thumbnail: 'https://picsum.photos/id/20/400/225', duration: '--:--', createdAt: '2023-10-23 15:20', status: 'draft' },
  { id: 'p3', title: '探店视频_最终版', thumbnail: 'https://picsum.photos/id/30/400/225', duration: '01:12', createdAt: '2023-10-22 09:15', status: 'completed' },
];

export const TEXT_TEMPLATES = [
  { title: '好物推荐', content: '家人们！今天给大家推荐一款超级好用的...' },
  { title: '知识讲解', content: '你知道吗？在量子力学中...' },
  { title: '团购探店', content: '只要99元，满满一大桌！今天我们来到了...' },
];