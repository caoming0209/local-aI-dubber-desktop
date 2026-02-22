# Research: AI数字人口播桌面客户端

**Branch**: `001-ai-dubber-desktop` | **Date**: 2026-02-19
**Status**: 所有 NEEDS CLARIFICATION 项已解决
**最后更新**: 2026-02-19（新增 UI 组件库选型、口型同步版本路线；Topic 5 更新：Element Plus → React 19 + Tailwind CSS；新增 Topic 8：Electron 渲染集成策略；Topic 9：Python 进程生命周期）

---

## Topic 1: Electron ↔ Python IPC 通信模式

### Decision
**使用本地 HTTP（FastAPI + uvicorn，绑定 127.0.0.1 随机端口）+ SSE（Server-Sent Events）双模式：**
- **一次性调用**（CRUD、设置读写、状态查询）：标准 HTTP REST
- **长任务进度流**（TTS 合成、口型同步、视频合成）：SSE 单向推送

启动握手：Python 进程启动后向 stdout 输出一行 `{"status": "ready", "port": 18432}`，Electron 主进程读取后切换至 HTTP 通信。

### Rationale
- SSE 天然单向推送，完美匹配「Python → Electron 推进度」的场景，无 WebSocket 双向握手开销
- FastAPI 通过 `sse-starlette` 原生支持 SSE，每条进度事件格式为 `data: {"step":"tts","pct":40}\n\n`
- 绑定 127.0.0.1（非 0.0.0.0），不触发 Windows 防火墙弹窗，无外网暴露风险
- 开发调试时可用 curl / DevTools Network 面板直接测试，stdin/stdout 方案无此能力
- 取消任务只需 `POST /api/task/{id}/cancel`，Python asyncio 取消对应 Task，简洁清晰

### Alternatives Considered
| 方案 | 结论 | 拒绝原因 |
|------|------|----------|
| stdin/stdout JSON-RPC | 拒绝 | 并发任务 + 进度流在单管道上需手动实现多路复用帧协议；Windows 管道缓冲问题难以调试 |
| WebSocket | 可行备选 | 双向全双工对此场景过度设计；SSE 更轻量 |
| Windows 命名管道 | 拒绝 | 底层 API 无标准请求/响应复用机制；调试困难 |
| HTTP 轮询（无 SSE） | 拒绝 | 250ms 轮询浪费 CPU，进度延迟高；SSE 严格优于此方案 |
| gRPC | 拒绝 | 需 Protobuf Schema 编译工具链；单机应用复杂度不值得 |

---

## Topic 2: 本地中文 TTS 模型选型（离线）

### Decision
**主选：CosyVoice3-0.5B（阿里巴巴达摩院）；备选：MB-iSTFT-VITS2（低配机器回退方案）**

**推荐音色映射**：

| 产品分类 | CosyVoice3-0.5B 对应 |
|----------|-----------------|
| 男声-沉稳 | `zh_male_zhongnian` 预设 |
| 女声-甜美 | `zh_female_xinliu` 预设 |
| 情感音 | Instruct 模式：`[emotion]joy/anger/sadness` 指令嵌入 |
| 方言音 | CosyVoice 方言变体或零样本克隆参考音频 |

**输出流水线**：
```
CosyVoice3.synthesize(text, speaker, speed_ratio)
  → WAV 24kHz → FFmpeg 音量归一化 + 重采样 16kHz → Wav2Lip 输入
```

### Rationale
1. **语音质量**：CosyVoice3-0.5B 在中文 Mandarin MOS 评测中高于 PaddleSpeech，接近商业 API
2. **情感控制**：Instruct 模式通过自然语言指令控制语速、情感、停顿（`[laughter]`、`[breath]`），直接满足 PRD 中情感强度调节需求
3. **零样本克隆**：3 秒参考音频即可克隆声音，为后续「自定义音色」功能预留扩展能力
4. **推理速度**：GPU（RTX 3060）约 15-20x 实时倍率（30 秒文本 ~1.5 秒合成）；CPU（i7）约 3-5x 实时（~8-10 秒），桌面应用可接受
5. **纯 PyTorch**：Wav2Lip 已依赖 PyTorch，两者共用同一框架无额外框架冲突
6. **Windows 离线部署**：模型权重约 1-2 GB，可在首次使用时下载，之后完全离线推理

**VITS 备选说明**：MB-iSTFT-VITS2 模型仅约 300 MB，CPU 推理更快，适合 8GB RAM 最低配置用户；但缺少 instruct-mode 情感控制，作为降级选项。

### Alternatives Considered
| 方案 | 结论 | 拒绝原因 |
|------|------|----------|
| PaddleSpeech | 拒绝 | 需引入 PaddlePaddle（额外 2-3 GB 依赖），与已有 PyTorch（Wav2Lip）框架冲突；Windows CUDA 支持历史不稳定 |
| Coqui TTS（XTTSv2） | 拒绝 | 项目已于 2024 年 1 月停止维护；中文质量低于 CosyVoice3-0.5B |
| edge-tts | 已排除 | 需要联网（Azure API），违反离线要求 |
| ChatTTS | 不推荐 | 针对短对话优化，长文案稳定性差；说话人控制有限 |
| GPT-SoVITS | 仅适用自定义音色 | 零样本克隆优秀，但作为主 TTS 引擎配置复杂；可作为「自定义音色克隆」的后期功能 |

---

## Topic 3: 作品库存储方案（SQLite vs JSON 文件）

### Decision
**使用 SQLite + Python 标准库 `sqlite3`（无 ORM），项目配置快照作为 JSON blob 存储在单一文本列中。**

核心表结构：
```sql
CREATE TABLE works (
    id           TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    file_path    TEXT NOT NULL,
    thumbnail_path TEXT,
    duration_s   REAL,
    aspect_ratio TEXT,    -- "16:9" | "9:16"
    created_at   INTEGER NOT NULL,  -- Unix 时间戳
    config_json  TEXT NOT NULL      -- 完整 ProjectConfig JSON 快照
);
CREATE INDEX idx_created_at ON works(created_at DESC);
CREATE INDEX idx_name       ON works(name);
CREATE INDEX idx_aspect     ON works(aspect_ratio);
```

**Schema 版本管理**：`PRAGMA user_version` 存储版本号，启动时检查并执行 `ALTER TABLE` 迁移，无需 Alembic。

**孤立记录处理**：应用启动时检查所有 `file_path` 是否存在（500 条 `Path.exists()` < 200ms），不存在的记录标记为孤立或自动删除。

### Rationale
- **PRD 查询需求**（按名称/日期搜索、按比例/日期筛选、多种排序、分页）在 JSON 文件方案下全部需要全量加载 + 内存过滤，O(n) 文件 I/O；SQLite 单次索引查询 < 5ms
- **config_json blob 设计**：「重新编辑」操作只需 `SELECT config_json FROM works WHERE id = ?`，无需多表 JOIN；schema 演进时只修改 JSON 字段，无需数据库迁移
- **stdlib-only**：无额外打包依赖，安装包体积不增加
- **单用户写入**：无并发写冲突，默认 WAL 关闭即可，后续如需并发可一行 PRAGMA 开启

### Alternatives Considered
| 方案 | 结论 | 拒绝原因 |
|------|------|----------|
| JSON 文件（每条作品一个文件） | 拒绝 | 搜索/筛选/排序需全量加载，HDD 上 500 文件 I/O 可感知卡顿 |
| JSON 文件 + 内存索引 | 拒绝 | 启动时需重建索引；一致性风险；复杂度接近但可靠性远低于 SQLite |
| SQLite + SQLAlchemy | 拒绝 | 5 个查询模式使用 ORM 层过度设计；额外 ~10MB 打包体积 |
| SQLite + peewee | 拒绝 | 同上 |
| LevelDB / RocksDB | 拒绝 | 键值存储无原生查询能力，需自实现过滤逻辑 |
| IndexedDB（Electron renderer） | 拒绝 | Python 后端无法访问；数据模型需在两处维护 |

---

## Topic 4: 离线授权——激活码 + 一次性联网验证

### Decision
**硬件指纹 = SHA-256(CPU ProcessorId | 主板 UUID | 主硬盘序列号)；本地存储 = AES-256-GCM 加密文件 `%APPDATA%\ZhiYingKouBo\license.dat`；激活服务器 = 轻量 Python Flask/FastAPI（约 150 行，5 个接口）。**

**指纹生成（2-of-3 容错策略）**：
```python
def get_fingerprint() -> str:
    cpu_id   = wmic("cpu", "ProcessorId")      or "UNKNOWN"
    mb_uuid  = wmic("csproduct", "UUID")       or "UNKNOWN"
    disk_sn  = wmic("diskdrive", "SerialNumber") or "UNKNOWN"
    raw = f"{cpu_id}|{mb_uuid}|{disk_sn}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]
```

服务器端存储三个组件哈希；重激活时 2/3 匹配视为同一设备，容忍内存/GPU 升级等小幅硬件变更。

**加密密钥派生**（防止 license.dat 跨机器复制）：
```python
SALT = b"zhiying_koubo_v1_salt_2024"   # 固化于二进制
aes_key = hashlib.pbkdf2_hmac('sha256', fingerprint.encode(), SALT, 100_000, dklen=32)
```

**激活后离线保证**：每次启动仅读取并解密本地 `license.dat`，验证 HMAC 完整性 + 设备指纹匹配，不联网。服务器仅在首次激活和主动解绑时各调用一次。

**激活码格式**：`XXXX-XXXX-XXXX-XXXX`（16 位 Base32 + Luhn 校验位），服务端预生成并存储 HMAC 哈希（明文不存入 DB）。

### Rationale
- **设备限制必须服务端强制**：纯本地验证无法防止激活码分享；2 台设备限制需服务端记录绑定关系
- **文件加密与机器绑定**：AES 密钥由设备指纹派生，将 license.dat 复制到其他机器解密失败，防止文件级破解
- **HMAC 防篡改**：即使攻击者解密文件，修改 `license_type` 或 `trial_count_used` 会使 HMAC 校验失败
- **CPU+主板+硬盘三因子**：单用 MAC 地址（VPN 变化）或 MachineGuid（重装丢失）都不够稳定；三因子组合稳定性高

### 防护级别说明
目标威胁模型：**普通用户分享激活码**，而非专业逆向工程师。
- PyInstaller 打包隐藏源码结构，防止 `python main.py` 直接运行
- PyArmor（免费版）仅对 `license/` 模块混淆，不全量混淆（避免严重影响启动速度）
- 不使用硬件加密狗、云端运行时验证等企业级手段（与离线需求冲突）

### Alternatives Considered
| 方案 | 结论 | 拒绝原因 |
|------|------|----------|
| 纯离线验证（无服务器） | 拒绝 | 无法强制执行设备数量限制；激活文件可被自由复制分发 |
| 云端运行时验证（每次启动联网） | 拒绝 | 违反「激活后完全离线」需求；服务器宕机时用户无法使用已付费软件 |
| Windows 注册表存储 | 拒绝 | 无内建加密；注册表位置是破解教程常见目标；文件方案可靠性相当 |
| 仅 MAC 地址指纹 | 拒绝 | VPN 改变 MAC；虚拟适配器干扰；极不稳定 |
| 企业级 DRM（SafeNet 等） | 拒绝 | 实现成本极高；损害用户体验；与消费品定位不符 |
| JWT 非对称签名（服务端） | 可补充 | 可作为激活响应的附加签名层；非替代方案 |

---

## Topic 5: 前端框架 & UI 样式方案选型

### Decision
**React 19 + Tailwind CSS + Zustand + React Router v7 + Lucide React**

采用此方案的直接原因：谷歌 AI 已生成完整的 React 19 初始前端项目（`智影口播-·-ai数字人视频助手/`），包含所有 8 个页面骨架（Home、SingleCreation、BatchCreation、AvatarManager、VoiceManager、WorksLibrary、Settings）、深色侧边栏布局（`bg-slate-900`）、路由配置（HashRouter），无需从零搭建。

**已有项目技术栈**：
| 包 | 版本 | 用途 |
|----|------|------|
| `react` | 19.2.4 | UI 框架 |
| `react-dom` | 19.2.4 | DOM 渲染 |
| `react-router-dom` | 7.13.0 | 客户端路由（HashRouter） |
| `lucide-react` | 0.574.0 | 图标库 |
| `typescript` | ~5.8.2 | 类型安全 |
| `vite` | ^6.2.0 | 构建工具 |
| `@vitejs/plugin-react` | ^5.0.0 | React HMR 插件 |

**待补充依赖**：
| 包 | 用途 |
|----|------|
| `tailwindcss` | 样式框架（当前项目用 CDN，需迁移为 npm 包） |
| `zustand` | 轻量状态管理（替代 Pinia） |
| `electron` | 桌面应用壳 |
| `electron-builder` | Windows NSIS 打包 |

### Rationale
- **复用现有工作**：谷歌 AI 生成的项目已完成所有页面路由和组件骨架，直接在此基础上开发节省大量初始工作
- **React 19 AI 代码生成质量高**：React 是全球使用量最大的前端框架，AI 训练数据最丰富，生成的组件代码质量高于 Vue 3
- **Tailwind CSS 与 React 配合成熟**：Tailwind 在 React 生态中是事实标准，AI 可靠生成 Tailwind 类名组合；无需学习特定组件库 API
- **Zustand 极简**：比 Pinia/Redux 体积小，API 更符合 React Hooks 模式，AI 生成的 store 代码几乎无模板代码
- **深色主题开箱即用**：已有项目采用 `bg-slate-900` 深色侧边栏 + `bg-gray-900` 主内容区，符合 PRD 主题要求
- **CDN → npm 迁移必要**：当前 Tailwind 通过 CDN 引入（`<script src="https://cdn.tailwindcss.com">`），生产打包时必须迁移为 npm 包以支持 tree-shaking 和 Electron 离线环境

### Alternatives Considered
| 方案 | 结论 | 备注 |
|------|------|------|
| Vue 3 + Element Plus（原方案） | 替换 | 现有 AI 生成项目为 React，重写 Vue 版本浪费资源 |
| React + Ant Design | 拒绝 | 引入重量级组件库；Tailwind 已满足需求；两者混用样式冲突风险高 |
| React + shadcn/ui | 可行备选 | 组件质量高，但与已有 Tailwind 纯类名风格一致性需额外调整 |
| Redux Toolkit | 拒绝 | 对单用户桌面应用状态复杂度过度；Zustand 足够 |

---

## Topic 6: 口型同步模型版本路线（Wav2Lip → MuseTalk）

### Decision
**v1.0 使用 Wav2Lip；v2.0 路线图升级为 MuseTalk（字节跳动）**

### v1.0 选择 Wav2Lip 的理由
- **发布于 2020 年**：是口型同步领域最成熟的开源方案，AI 训练数据中有大量集成代码示例
- **AI 代码生成质量高**：集成方式固定（输入视频 + 音频，输出视频），AI 可以直接生成 Python 封装代码，错误率低
- **Windows 离线部署成熟**：PyTorch 依赖清晰，CUDA/CPU 双模式均有完整文档和社区案例
- **API 简洁**：核心调用为单函数，参数少，集成门槛低

### v1.0 Wav2Lip 的已知局限
- 口型同步时人脸区域有轻微"粘贴感"（边缘融合不自然）
- 对斜侧脸角度效果下降明显
- 不支持头部运动自然变化

### v2.0 升级 MuseTalk 的理由
- **字节跳动 2024 年发布**：实时推理能力，面部融合更自然，头部姿态保持更真实
- **目前不作为 v1.0 选型**：发布时间短（训练数据少，AI 生成代码质量低）；多模型组件集成复杂；社区 Windows 部署案例少
- **升级时机**：v1.0 上线后，收集用户对视频质量的反馈，若口型自然度是主要投诉点，则启动 MuseTalk 迁移

### 迁移成本估算
由于两者都是「输入视频 + 音频 → 输出视频」的接口模式，v2.0 迁移只需替换 `lipsync_engine.py` 的实现，上层 FastAPI 路由和前端代码无需修改。迁移隔离性良好。

---

## Topic 7: 二进制保护方案

### Decision
**electron-builder（前端打包）+ PyInstaller（Python 引擎打包）+ Nuitka 单独编译 `license/` 模块**

### Rationale
- **PyInstaller**：将 Python 引擎打包为独立 `.exe`，隐藏源码目录结构，阻止 `python main.py` 直接运行。标准方案，构建速度快
- **Nuitka 仅用于 `license/` 模块**：将授权验证逻辑（指纹生成、AES 解密、HMAC 校验）编译为原生 C 扩展（`.pyd`），逆向难度远高于 PyInstaller 的 bytecode（`.pyc`）方案。全量 Nuitka 编译收益边际递减，且大幅增加构建时间
- **不使用 PyArmor**：免费版混淆质量有限，已有成熟的自动化解混淆工具；付费版成本较高且需要持续订阅

### 威胁模型
目标是防御**普通用户分享激活码**，而非专业逆向工程师。上述方案对此威胁模型足够，且维护成本低。

### Alternatives Considered
| 方案 | 结论 | 拒绝原因 |
|------|------|----------|
| 全量 Nuitka 编译 | 拒绝 | 首次编译耗时 15-30 分钟；对非关键模块保护收益低 |
| PyArmor 免费版 | 拒绝 | 混淆可被现有工具自动还原；保护强度不足 |
| PyArmor 付费版 | 备选 | 若 Nuitka 集成遇到问题可作为替代；需评估授权费用 |
| 硬件加密狗 | 拒绝 | UX 差；成本高；与产品消费品定位不符 |

---



| 主题 | 决策 | 核心理由 |
|------|------|----------|
| IPC 通信 | FastAPI HTTP + SSE | 一次性调用与进度流分离；可调试；无管道帧协议 |
| 中文 TTS | CosyVoice3-0.5B（主）+ VITS（低配备选） | 中文质量最优；Instruct 情感控制；纯 PyTorch 无框架冲突 |
| 存储 | SQLite（stdlib sqlite3）+ JSON config blob | 索引查询满足搜索筛选；无 ORM 依赖；config blob 简化重编辑 |
| 授权激活 | 一次联网激活 + AES-256-GCM 本地文件 + CPU/主板/硬盘指纹 | 服务端强制设备限制；机器绑定防文件复制；激活后永久离线 |
| 前端框架 & 样式 | React 19 + Tailwind CSS + Zustand + React Router v7 | 复用谷歌 AI 生成的初始项目；React 训练数据最丰富；Tailwind 无组件库 API 学习成本 |
| 口型同步（v1.0） | Wav2Lip | 成熟稳定，AI 代码生成质量高，快速交付 |
| 口型同步（v2.0） | MuseTalk（路线图） | 效果更自然，待产品验证后升级 |
| 打包保护 | electron-builder + PyInstaller + Nuitka（license 模块） | license 模块原生编译，防逆向能力显著高于 PyArmor |
