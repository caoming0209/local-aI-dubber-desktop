import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

from huggingface_hub import snapshot_download

models_dir = os.path.expanduser("~/Documents/local-aI-dubber-desktop/models")
cosyvoice_dir = os.path.join(models_dir, "cosyvoice2", "CosyVoice2-0.5B")

os.makedirs(cosyvoice_dir, exist_ok=True)

print("开始下载 CosyVoice2-0.5B 模型（使用国内镜像）...")
print(f"目标目录: {cosyvoice_dir}")
print("这可能需要几分钟时间，请耐心等待...")

try:
    result_dir = snapshot_download(
        repo_id="FunAudioLLM/CosyVoice2-0.5B",
        local_dir=cosyvoice_dir,
    )
    print(f"\n✅ 模型下载成功！")
    print(f"保存位置: {result_dir}")
except Exception as e:
    print(f"\n❌ 下载失败: {e}")
