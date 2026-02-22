"""Voice configuration: maps voice_id to CosyVoice3 inference parameters."""


# CosyVoice3 supports these modes:
#   "zero_shot"      — clone from prompt audio + prompt text (inference_zero_shot)
#   "cross_lingual"  — cross-lingual synthesis with prompt audio only
#   "instruct2"      — instruction-guided synthesis (inference_instruct2)
#
# <|endofprompt|> marker placement is handled by TTSEngine.synthesize(), NOT here.
# - prompt_text: the actual spoken content of prompt_wav (no markers needed)
# - instruct_text: the instruction text (no markers needed, engine adds prefix + marker)

VOICE_CONFIGS = {
    # ─── Standard male voices ───────────────────────────────
    "voice_male_01": {
        "name": "标准男声-浩然",
        "mode": "zero_shot",
        "speaker_id": None,
        "instruct_text": "用标准普通话朗读这段话。",
        "prompt_wav": "voices/male_haoran/prompt.wav",
        "prompt_text": "大家好，我是浩然，很高兴为您服务。",
    },
    "voice_male_02": {
        "name": "磁性男声-子轩",
        "mode": "cross_lingual",
        "speaker_id": None,
        "instruct_text": "用低沉磁性的声音朗读这段话。",
        "prompt_wav": "voices/male_zixuan/prompt.wav",
        "prompt_text": "大家好，我是子轩，一个喜欢讲故事的人。",
    },

    # ─── Standard female voices ─────────────────────────────
    "voice_female_01": {
        "name": "标准女声-思琪",
        "mode": "cross_lingual",
        "speaker_id": None,
        "instruct_text": "用温柔清晰的女声朗读这段话。",
        "prompt_wav": "voices/female_siqi/prompt.wav",
        "prompt_text": "大家好，我是思琪，很高兴认识你。",
    },
    "voice_female_02": {
        "name": "甜美女声-雨萱",
        "mode": "cross_lingual",
        "speaker_id": None,
        "instruct_text": "用甜美活泼的声音朗读这段话。",
        "prompt_wav": "voices/female_yuxuan/prompt.wav",
        "prompt_text": "嗨，我是雨萱，很高兴认识你。",
    },

    # ─── Emotional voices ───────────────────────────────────
    "voice_emotional_01": {
        "name": "情感男声-明远",
        "mode": "cross_lingual",
        "speaker_id": None,
        "instruct_text": "用富有感染力的声音朗读这段话。",
        "prompt_wav": "voices/emotional_mingyuan/prompt.wav",
        "prompt_text": "在面对挑战时，他展现了非凡的勇气与智慧。",
    },
    "voice_emotional_02": {
        "name": "情感女声-晓月",
        "mode": "cross_lingual",
        "speaker_id": None,
        "instruct_text": "用温柔细腻的声音朗读这段话。",
        "prompt_wav": "voices/emotional_xiaoyue/prompt.wav",
        "prompt_text": "收到好友从远方寄来的生日礼物，那份意外的惊喜让我心中充满了快乐。",
    },

    # ─── Dialect voices ─────────────────────────────────────
    "voice_dialect_01": {
        "name": "粤语男声-阿辉",
        "mode": "cross_lingual",
        "speaker_id": None,
        "instruct_text": "请用广东话说这句话。",
        "prompt_wav": "voices/dialect_ahui/prompt.wav",
        "prompt_text": "大家好，我系阿辉，好高兴见到你哋。",
    },
    "voice_dialect_02": {
        "name": "四川话女声-小蓉",
        "mode": "cross_lingual",
        "speaker_id": None,
        "instruct_text": "请用四川话说这句话。",
        "prompt_wav": "voices/dialect_xiaorong/prompt.wav",
        "prompt_text": "你好嘛，我是小蓉，欢迎来到四川。",
    },
}


def get_voice_config(voice_id: str) -> dict:
    """Get voice configuration by ID. Returns default config if not found."""
    config = VOICE_CONFIGS.get(voice_id)
    if config:
        return config
    # Fallback: use zero_shot mode with default prompt
    return {
        "name": "默认女声",
        "mode": "zero_shot",
        "speaker_id": None,
        "instruct_text": "用标准普通话朗读这段话。",
        "prompt_wav": "voices/female_siqi/prompt.wav",
        "prompt_text": "大家好，我是思琪，很高兴认识你。",
    }
