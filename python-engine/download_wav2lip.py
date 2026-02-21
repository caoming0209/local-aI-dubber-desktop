import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

import requests

models_dir = os.path.expanduser("~/Documents/local-aI-dubber-desktop/models")
wav2lip_dir = os.path.join(models_dir, "wav2lip")
os.makedirs(wav2lip_dir, exist_ok=True)

print("开始下载 Wav2Lip 模型（从 Hugging Face）...")
print(f"目标目录: {wav2lip_dir}")

# 尝试从不同的 Hugging Face 仓库下载
download_urls = [
    "https://hf-mirror.com/ali-vilab/wav2lip/resolve/main/wav2lip_gan.pth",
    "https://hf-mirror.com/vinthony/wav2lip/resolve/main/wav2lip_gan.pth",
    "https://hf-mirror.com/jeffreyyihui/wav2lip/resolve/main/wav2lip_gan.pth",
]

model_path = os.path.join(wav2lip_dir, "wav2lip_gan.pth")

for i, url in enumerate(download_urls, 1):
    print(f"\n尝试下载源 {i}/{len(download_urls)}: {url}")
    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        block_size = 8192
        downloaded = 0
        
        if total_size > 0:
            print(f"文件大小: {total_size / (1024*1024):.2f} MB")
            print("开始下载...")
        else:
            print("开始下载...")
        
        with open(model_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=block_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\r下载进度: {percent:.1f}% ({downloaded}/{total_size} bytes)", end='')
        
        if downloaded > 1024*1024*50:  # 大于 50MB 才认为是有效模型
            print(f"\n\n✅ Wav2Lip 模型下载成功！")
            print(f"保存位置: {model_path}")
            print(f"文件大小: {downloaded / (1024*1024):.2f} MB")
            break
        else:
            print(f"\n❌ 下载的文件太小，可能不是有效模型 ({downloaded} bytes)")
            if os.path.exists(model_path):
                os.remove(model_path)
            
    except Exception as e:
        print(f"\n❌ 下载失败: {e}")
        if i < len(download_urls):
            print("尝试下一个下载源...")
        else:
            print("\n所有下载源都失败了。")
            print("\n请手动下载 wav2lip_gan.pth 文件并放到以下目录：")
            print(f"  {wav2lip_dir}")
