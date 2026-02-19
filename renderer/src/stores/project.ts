import { create } from 'zustand';
import type {
  SinglePipelineRequest,
  VoiceParams,
  Background,
  SubtitleConfig,
  BgmConfig,
  AspectRatio,
} from '@shared/ipc-types';

interface ProjectState {
  // Current creation config
  script: string;
  voiceId: string;
  voiceParams: VoiceParams;
  digitalHumanId: string;
  background: Background;
  aspectRatio: AspectRatio;
  subtitle: SubtitleConfig;
  bgm: BgmConfig;
  outputName: string;

  // Wizard state
  currentStep: number;

  // Actions
  setScript: (script: string) => void;
  setVoiceId: (id: string) => void;
  setVoiceParams: (params: Partial<VoiceParams>) => void;
  setDigitalHumanId: (id: string) => void;
  setBackground: (bg: Background) => void;
  setAspectRatio: (ratio: AspectRatio) => void;
  setSubtitle: (config: Partial<SubtitleConfig>) => void;
  setBgm: (config: Partial<BgmConfig>) => void;
  setOutputName: (name: string) => void;
  setCurrentStep: (step: number) => void;
  reset: () => void;
  toRequest: () => SinglePipelineRequest;
  loadFromConfig: (config: Partial<SinglePipelineRequest>) => void;
}

const DEFAULT_STATE = {
  script: '',
  voiceId: '',
  voiceParams: { speed: 1.0, volume: 1.0, emotion: 0.5 },
  digitalHumanId: '',
  background: { type: 'solid_color' as const, value: '#F5F5F5' },
  aspectRatio: '9:16' as AspectRatio,
  subtitle: { enabled: true, font_family: 'Microsoft YaHei', font_size: 30, color: '#FFFFFF', position: 'bottom_center' as const },
  bgm: { enabled: false, bgm_id: null, custom_path: null, voice_volume: 1.0, bgm_volume: 0.5 },
  outputName: '',
  currentStep: 1,
};

export const useProjectStore = create<ProjectState>((set, get) => ({
  ...DEFAULT_STATE,

  setScript: (script) => set({ script }),
  setVoiceId: (voiceId) => set({ voiceId }),
  setVoiceParams: (params) => set((s) => ({ voiceParams: { ...s.voiceParams, ...params } })),
  setDigitalHumanId: (digitalHumanId) => set({ digitalHumanId }),
  setBackground: (background) => set({ background }),
  setAspectRatio: (aspectRatio) => set({ aspectRatio }),
  setSubtitle: (config) => set((s) => ({ subtitle: { ...s.subtitle, ...config } })),
  setBgm: (config) => set((s) => ({ bgm: { ...s.bgm, ...config } })),
  setOutputName: (outputName) => set({ outputName }),
  setCurrentStep: (currentStep) => set({ currentStep }),

  reset: () => set(DEFAULT_STATE),

  toRequest: () => {
    const s = get();
    return {
      script: s.script,
      voice_id: s.voiceId,
      voice_params: s.voiceParams,
      digital_human_id: s.digitalHumanId,
      background: s.background,
      aspect_ratio: s.aspectRatio,
      subtitle: s.subtitle,
      bgm: s.bgm,
      output_name: s.outputName || `video_${Date.now()}`,
    };
  },

  loadFromConfig: (config) => {
    set({
      script: config.script ?? DEFAULT_STATE.script,
      voiceId: config.voice_id ?? DEFAULT_STATE.voiceId,
      voiceParams: config.voice_params ?? DEFAULT_STATE.voiceParams,
      digitalHumanId: config.digital_human_id ?? DEFAULT_STATE.digitalHumanId,
      background: config.background ?? DEFAULT_STATE.background,
      aspectRatio: config.aspect_ratio ?? DEFAULT_STATE.aspectRatio,
      subtitle: config.subtitle ?? DEFAULT_STATE.subtitle,
      bgm: config.bgm ?? DEFAULT_STATE.bgm,
      outputName: config.output_name ?? DEFAULT_STATE.outputName,
      currentStep: 1,
    });
  },
}));
