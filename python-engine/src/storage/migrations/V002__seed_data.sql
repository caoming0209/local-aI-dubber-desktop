-- V002: Seed official digital humans and builtin BGM tracks

-- ─── Official Digital Humans (10 entries) ───────────────────────
INSERT OR IGNORE INTO digital_humans (id, name, category, source, thumbnail_path, preview_video_path, adapted_video_path, adaptation_status, is_favorited, created_at, sort_order)
VALUES
  ('dh_official_01', '商务男士-李明', 'business', 'official', '', '', '', 'ready', 0, '2025-01-01T00:00:00Z', 1),
  ('dh_official_02', '商务女士-王芳', 'business', 'official', '', '', '', 'ready', 0, '2025-01-01T00:00:00Z', 2),
  ('dh_official_03', '新闻主播-张伟', 'news', 'official', '', '', '', 'ready', 0, '2025-01-01T00:00:00Z', 3),
  ('dh_official_04', '新闻主播-刘婷', 'news', 'official', '', '', '', 'ready', 0, '2025-01-01T00:00:00Z', 4),
  ('dh_official_05', '教育讲师-陈老师', 'education', 'official', '', '', '', 'ready', 0, '2025-01-01T00:00:00Z', 5),
  ('dh_official_06', '生活博主-小美', 'lifestyle', 'official', '', '', '', 'ready', 0, '2025-01-01T00:00:00Z', 6),
  ('dh_official_07', '科技达人-小杰', 'tech', 'official', '', '', '', 'ready', 0, '2025-01-01T00:00:00Z', 7),
  ('dh_official_08', '医疗顾问-赵医生', 'medical', 'official', '', '', '', 'ready', 0, '2025-01-01T00:00:00Z', 8),
  ('dh_official_09', '健身教练-阿强', 'fitness', 'official', '', '', '', 'ready', 0, '2025-01-01T00:00:00Z', 9),
  ('dh_official_10', '旅行达人-小雅', 'travel', 'official', '', '', '', 'ready', 0, '2025-01-01T00:00:00Z', 10);

-- ─── Builtin BGM Tracks (10 entries) ────────────────────────────
INSERT OR IGNORE INTO bgm_tracks (id, name, category, source, file_path, duration_seconds)
VALUES
  ('bgm_builtin_01', '轻快节奏', 'upbeat', 'builtin', 'bgm/upbeat_01.mp3', 120.0),
  ('bgm_builtin_02', '活力四射', 'upbeat', 'builtin', 'bgm/upbeat_02.mp3', 90.0),
  ('bgm_builtin_03', '欢快旋律', 'upbeat', 'builtin', 'bgm/upbeat_03.mp3', 105.0),
  ('bgm_builtin_04', '舒缓钢琴', 'soothing', 'builtin', 'bgm/soothing_01.mp3', 180.0),
  ('bgm_builtin_05', '宁静时光', 'soothing', 'builtin', 'bgm/soothing_02.mp3', 150.0),
  ('bgm_builtin_06', '温暖午后', 'soothing', 'builtin', 'bgm/soothing_03.mp3', 135.0),
  ('bgm_builtin_07', '恢弘大气', 'grand', 'builtin', 'bgm/grand_01.mp3', 160.0),
  ('bgm_builtin_08', '史诗交响', 'grand', 'builtin', 'bgm/grand_02.mp3', 200.0),
  ('bgm_builtin_09', '科技未来', 'upbeat', 'builtin', 'bgm/upbeat_04.mp3', 110.0),
  ('bgm_builtin_10', '自然之声', 'soothing', 'builtin', 'bgm/soothing_04.mp3', 170.0);

-- ─── Builtin Voice Models (8 entries) ───────────────────────────
INSERT OR IGNORE INTO voice_models (id, name, category, description, model_size_mb, download_status, download_url, is_emotional, sort_order)
VALUES
  ('voice_male_01', '标准男声-浩然', 'male', '沉稳大气的标准男声，适合新闻播报和商务场景', 850.0, 'not_downloaded', 'models/cosyvoice2/male_haoran', 0, 1),
  ('voice_male_02', '磁性男声-子轩', 'male', '低沉磁性男声，适合故事讲述和深度内容', 850.0, 'not_downloaded', 'models/cosyvoice2/male_zixuan', 1, 2),
  ('voice_female_01', '标准女声-思琪', 'female', '清晰温柔的标准女声，适合教育和生活类内容', 850.0, 'not_downloaded', 'models/cosyvoice2/female_siqi', 0, 3),
  ('voice_female_02', '甜美女声-雨萱', 'female', '甜美活泼的女声，适合短视频和娱乐内容', 850.0, 'not_downloaded', 'models/cosyvoice2/female_yuxuan', 1, 4),
  ('voice_emotional_01', '情感男声-明远', 'emotional', '富有感染力的男声，支持多种情感表达', 1200.0, 'not_downloaded', 'models/cosyvoice2/emotional_mingyuan', 1, 5),
  ('voice_emotional_02', '情感女声-晓月', 'emotional', '细腻动人的女声，支持多种情感表达', 1200.0, 'not_downloaded', 'models/cosyvoice2/emotional_xiaoyue', 1, 6),
  ('voice_dialect_01', '粤语男声-阿辉', 'dialect', '地道粤语男声，适合粤语区域内容', 900.0, 'not_downloaded', 'models/cosyvoice2/dialect_ahui', 0, 7),
  ('voice_dialect_02', '四川话女声-小蓉', 'dialect', '亲切自然的四川话女声', 900.0, 'not_downloaded', 'models/cosyvoice2/dialect_xiaorong', 0, 8);
