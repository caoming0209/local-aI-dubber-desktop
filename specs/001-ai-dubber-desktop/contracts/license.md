# License & Activation API Contract

**Branch**: `001-ai-dubber-desktop` | **Date**: 2026-02-19

---

## 概述

授权模块分为两部分：
1. **本地状态管理**：读写 `license.dat`（AES-256 加密），所有操作在 Python 后端执行。
2. **一次性远程验证**：激活时调用激活服务器，验证激活码 + 绑定设备指纹。激活后本地持久化状态，日常使用不再联网。

---

## 本地 IPC 接口（前端调用 Python 后端）

### GET /api/license/status

获取当前授权状态。

**Response**:
```json
{
  "success": true,
  "data": {
    "type": "trial",
    "used_trial_count": 3,
    "max_trial_count": 5,
    "remaining_trial_count": 2,
    "activated_at": null,
    "activation_code_masked": null,
    "device_count": 1,
    "max_device_count": 2
  }
}
```

已激活示例：
```json
{
  "success": true,
  "data": {
    "type": "activated",
    "used_trial_count": 5,
    "max_trial_count": 5,
    "remaining_trial_count": 0,
    "activated_at": "2026-02-19T10:00:00Z",
    "activation_code_masked": "XXXX-XXXX-****-****",
    "device_count": 1,
    "max_device_count": 2
  }
}
```

---

### POST /api/license/activate

输入激活码，触发一次性远程验证并绑定设备。

**Request**:
```json
{
  "activation_code": "ABCD-1234-EFGH-5678"
}
```

**Response 成功** (200):
```json
{
  "success": true,
  "data": {
    "type": "activated",
    "activated_at": "2026-02-19T10:05:00Z",
    "activation_code_masked": "ABCD-1234-****-****",
    "device_count": 1,
    "max_device_count": 2
  }
}
```

**Response 失败** (200，success=false):
```json
{
  "success": false,
  "error": {
    "code": "LICENSE_INVALID_CODE",
    "message": "激活码无效，请检查输入是否正确"
  }
}
```

可能的错误码：
- `LICENSE_INVALID_CODE`: 激活码不存在或已被撤销
- `LICENSE_DEVICE_LIMIT`: 该激活码已绑定 2 台设备，请先解绑旧设备
- `LICENSE_NETWORK_ERROR`: 网络不可用，激活需要联网，请检查网络后重试
- `LICENSE_ALREADY_ACTIVATED`: 当前设备已激活

---

### POST /api/license/unbind

解绑当前设备（迁移授权用）。需联网操作。

**Request**: 无（自动使用当前设备指纹）

**Response 成功**:
```json
{
  "success": true,
  "data": {
    "type": "trial",
    "message": "当前设备已解绑，激活码名额已释放，可在新设备激活"
  }
}
```

**Response 失败**:
```json
{
  "success": false,
  "error": {
    "code": "LICENSE_NETWORK_ERROR",
    "message": "解绑需要联网，请检查网络后重试"
  }
}
```

---

### POST /api/license/consume-trial

生成视频成功后扣减试用次数。此接口由 pipeline 路由内部调用，前端不直接调用。

**Request**: `{"count": 1}`

**Response**:
```json
{
  "success": true,
  "data": {
    "remaining_trial_count": 1,
    "trial_exhausted": false
  }
}
```

试用耗尽时：
```json
{
  "success": true,
  "data": {
    "remaining_trial_count": 0,
    "trial_exhausted": true
  }
}
```

---

## 激活服务器接口（Python 后端调用，前端不直接访问）

激活服务器为轻量级 REST API，Python 后端在激活/解绑时调用一次。

### POST {ACTIVATION_SERVER}/api/v1/activate

**Request**:
```json
{
  "activation_code": "ABCD-1234-EFGH-5678",
  "device_fingerprint": "sha256:a1b2c3d4e5f6...",
  "app_version": "1.0.0"
}
```

**Response 成功**:
```json
{
  "success": true,
  "license": {
    "activation_code": "ABCD-1234-EFGH-5678",
    "device_count": 1,
    "max_device_count": 2,
    "activated_at": "2026-02-19T10:05:00Z"
  }
}
```

---

### POST {ACTIVATION_SERVER}/api/v1/unbind

**Request**:
```json
{
  "activation_code": "ABCD-1234-EFGH-5678",
  "device_fingerprint": "sha256:a1b2c3d4e5f6..."
}
```

**Response**:
```json
{"success": true, "remaining_slots": 2}
```

---

## 设备指纹生成策略（Windows）

硬件指纹由以下信息拼接后 SHA-256 哈希：
1. CPU ID（WMI: `Win32_Processor.ProcessorId`）
2. 主板序列号（WMI: `Win32_BaseBoard.SerialNumber`）
3. 系统磁盘序列号（WMI: `Win32_DiskDrive.SerialNumber`，取第一块）

```python
fingerprint = sha256(f"{cpu_id}|{motherboard_sn}|{disk_sn}".encode()).hexdigest()
```

**容错**: 任意一项获取失败时，用固定占位符 "UNKNOWN" 替代，保证指纹始终可生成。

---

## 本地授权文件加密方案

- **加密算法**: AES-256-GCM
- **密钥派生**: 设备指纹 + 固定 salt 经 PBKDF2 派生 256-bit 密钥
- **文件格式**: `{nonce(12B)}{ciphertext}{tag(16B)}`，Base64 编码后写入 `license.dat`
- **目的**: 防止直接复制 `license.dat` 到其他设备使用（不同设备指纹 → 不同密钥 → 解密失败 → 重置为 trial 状态）
