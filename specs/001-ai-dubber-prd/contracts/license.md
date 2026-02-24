# License Contract (Local Engine)

Base URL: `http://127.0.0.1:{port}/api`

## GET `/license/status`

Return current license state.

**Response**

```json
{
  "type": "trial",
  "used_trial_count": 0,
  "activation_code_masked": "ABCD-****-WXYZ",
  "activated_at": null,
  "device_fingerprint": "sha256:..."
}
```

## POST `/license/activate`

Activate with code (requires network). Must not block offline generation flows.

**Request**

```json
{"activation_code": "ABCD-..."}
```

**Response**

```json
{"type": "activated", "activated_at": "2026-02-24"}
```

## POST `/license/unbind`

Unbind current device (requires network).

**Request**

```json
{"activation_code": "ABCD-..."}
```

## POST `/license/consume-trial`

Consume one trial use (internal call).

**Response**

```json
{"used_trial_count": 1}
```

## Error codes

- `LICENSE_TRIAL_EXHAUSTED`
- `LICENSE_INVALID_CODE`
- `LICENSE_DEVICE_LIMIT`
- `LICENSE_NETWORK_ERROR`
- `INTERNAL_ERROR`
