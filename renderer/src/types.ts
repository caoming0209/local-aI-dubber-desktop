export enum RoutePath {
  HOME = '/',
  SINGLE_CREATE = '/create/single',
  BATCH_CREATE = '/create/batch',
  AVATARS = '/avatars',
  VOICES = '/voices',
  WORKS = '/works',
  SETTINGS = '/settings',
  HELP = '/help'
}

export interface Avatar {
  id: string;
  name: string;
  thumbnail: string;
  category: 'official' | 'custom';
  tags: string[];
}

export interface Voice {
  id: string;
  name: string;
  gender: 'male' | 'female';
  style: string;
  isDownloaded: boolean;
}

export interface Project {
  id: string;
  title: string;
  thumbnail: string;
  duration: string;
  createdAt: string;
  status: 'draft' | 'completed' | 'processing';
}

export enum Step {
  TEXT = 1,
  VOICE = 2,
  AVATAR = 3,
  SETTINGS = 4,
  GENERATE = 5
}