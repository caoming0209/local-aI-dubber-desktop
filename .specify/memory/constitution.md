<!--
Sync Impact Report
- Version change: 1.0.0 → 1.0.1
- Modified principles: None
- Added sections: None
- Removed sections: None
- Templates review (no edits required):
  - ✅ .specify/templates/plan-template.md
  - ✅ .specify/templates/spec-template.md
  - ✅ .specify/templates/tasks-template.md
  - ✅ .specify/templates/checklist-template.md
  - ✅ .specify/templates/agent-file-template.md
- Follow-up TODOs: None
-->

# 智影口播 · AI数字人视频助手 Constitution

## Core Principles

### I. 离线优先与隐私保护
- 系统 MUST 在无网络环境下完成核心生成闭环（单条/批量生成、字幕输出、作品访问）。
- 系统 MUST 默认不上传、不收集用户的文案/图片/音频/视频等内容；核心流程不依赖任何云端服务。
- 任何需要联网的能力（如激活验证、模型下载、检查更新）MUST 与离线生成解耦，且在 UI 上明确标识。

### II. 本地 IPC 边界与安全
- 前端与后端通信 MUST 仅绑定 `127.0.0.1:{random_port}`，不得对外网卡监听。
- 长任务进度 MUST 通过 SSE 单向推送；一次性调用使用标准 REST。
- 引擎启动握手 MUST 通过 stdout 输出就绪信息（`{"status":"ready","port":...}`）并由 Electron 读取后再开始 HTTP 通信。
- 任何跨进程输入（文案、路径、配置）MUST 在边界处做校验与错误码归一化，避免崩溃与不可理解错误。

### III. 可恢复的作业与可观测进度
- 生成任务 MUST 具有稳定的作业标识（job_id），并可查询作业状态快照用于断线恢复。
- UI MUST 持续展示总体进度与当前阶段描述；批量任务 MUST 展示每条状态（等待/执行中/成功/失败）与最终汇总。
- 取消操作 MUST 需要确认；取消后 MUST 清理临时文件，且已完成产物不被误删。
- 批量断点续传 MUST 以“按条目续跑”为粒度：异常退出时正在执行的条目视为未完成，恢复时从头重跑该条目。

### IV. 资源感知与稳定性优先
- 生成过程中 MUST 展示资源状态（至少 CPU/内存/显存），并以不低于每 2 秒 1 次频率更新。
- 当资源压力达到预警阈值时 MUST 提示用户且不遮挡核心操作区。
- 当无法安全继续时 MUST 采取可控降级或可控中断以避免崩溃，并给出可执行建议（例如切换 720P、缩小批量规模、改为 CPU 模式）。
- 批量任务 MUST 严格串行执行，避免并行推理导致内存/显存不可控。

### V. 最小复杂度与可维护性
- 实现 MUST 优先采用现有技术栈与既有目录结构（Electron/React/TypeScript + Python/FastAPI）。
- 变更 MUST 聚焦当前需求，避免为“未来可能”引入抽象、框架或跨层耦合。
- 对用户可见行为的变更 MUST 可验证：优先补齐/更新现有测试体系中的对应测试；如不添加测试，PR MUST 写明理由与替代验证方式。

## 产品与技术约束

- **目标平台**：Windows 10/11 x64，最终以 `.exe` 安装包分发。
- **核心能力离线**：除激活/模型下载/更新检查外，核心生成与作品访问 MUST 离线可用。
- **隐私**：用户素材与产物本地存储；不得引入默认上传、默认同步或默认遥测。
- **输出策略**：单条生成默认输出 1080P，允许切换 720P；字幕默认同时输出外置字幕文件与视频内嵌字幕。
- **安全上限**：批量导入条目数单批 MUST ≤ 30；超过时提示并限制本次任务规模。
- **存储边界**：
  - 作品库与配置快照等结构化数据存储在本地 SQLite。
  - 应用设置使用本地 JSON 文件。
  - 授权状态使用本地加密文件（设备指纹派生密钥）。
  - 所有 `*_path` 字段存储绝对路径。

## 开发流程与质量门禁

- **变更最小化**：除非需求明确，避免跨模块重构与“顺手优化”。
- **错误码与可理解提示**：用户输入不合规（图片/音频/文案/空间不足/GPU 不可用等）MUST 返回明确原因与修正建议。
- **回归验证**：
  - 前端：优先使用 Vitest + React Testing Library 覆盖关键交互与状态逻辑。
  - 后端：优先使用 pytest 覆盖核心业务与错误码映射。
  - E2E：对端到端闭环与批量断点续传等高风险流程使用 Playwright 验证（当项目已有对应用例时）。
- **离线门禁**：任何引入网络请求的变更 MUST 明确其触发条件，并确保不影响离线闭环。

## Governance

- 本宪章在工程实践层面具有最高优先级；与其它约定冲突时，以本宪章为准。
- 修订流程：
  - 任何修订 MUST 通过 PR 修改 `.specify/memory/constitution.md`。
  - PR 描述 MUST 说明：变更动机、涉及原则/约束、迁移影响（若有）。
- 版本策略（SemVer）：
  - MAJOR：移除/重定义原则或治理规则，导致既有流程需要重大调整。
  - MINOR：新增原则/新增重要门禁/显著扩展治理范围。
  - PATCH：澄清、措辞调整、拼写与非语义性修改。
- 合规检查期望：
  - `/speckit.plan` 的 “Constitution Check” 部分 MUST 根据本文件列出本次特性计划需满足的门禁项。
  - 评审者 MUST 在 PR review 中明确检查离线性、隐私边界、任务可恢复性与资源稳定性风险。
- 运行时开发指引以 `CLAUDE.md` 与 `specs/001-ai-dubber-prd/spec.md` 为准；本宪章提供不可违背的约束与门禁。

**Version**: 1.0.1 | **Ratified**: 2026-02-24 | **Last Amended**: 2026-02-24
