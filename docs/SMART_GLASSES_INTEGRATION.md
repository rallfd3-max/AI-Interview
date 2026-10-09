# Smart Glasses Integration

## Architecture

```text
Smart Glasses (vendor adapter or MockGlassesBridge)
                 ↕ device transport
Phone Gateway: CandidateGateway + ServerApiClient
                 ↕ HTTPS REST
Java Spring Boot: /api/glasses/*
                 ↕
Existing Candidate / Job / Interview services and MySQL
```

The glasses adapter and the phone gateway do not connect to MySQL and do not call the Python AI service. The phone's `ServerApiClient` calls Java only.

## Phone module

The new module is `huiyi-interviewer/glasses/`.

| Component | Responsibility |
|---|---|
| `ServerApiClient` | Java HTTP client, timeout/error mapping and response validation |
| `CandidateGateway` | Owns the candidate search/selection state machine |
| `IGlassesBridge` | Hardware-neutral glasses contract |
| `MockGlassesBridge` | In-memory bridge for demo and automated verification |
| `VendorGlassesBridge` | Delegates to a future vendor SDK adapter; does not invent SDK calls |

## Configuration

Set this key through the uni-app build environment or secure device configuration:

```env
AI_INTERVIEWER_SERVER_BASE_URL=https://your-java-server.example
```

The committed example intentionally leaves the value empty. Empty configuration raises `SERVER_NOT_CONFIGURED`; the client never falls back to a LAN address or localhost.

## Device message contract

Glasses → phone:

```json
{"type":"SEARCH_CANDIDATE","payload":{"name":"张三"}}
```

```json
{"type":"SELECT_CANDIDATE","payload":{"candidateId":"202"}}
```

Phone → glasses:

```json
{"type":"CANDIDATE_MATCHES","payload":{"queryName":"张三","count":2,"candidates":[]}}
```

```json
{"type":"CANDIDATE_CONTEXT","payload":{"candidateId":"202","realName":"张三"}}
```

```json
{"type":"LOADING","payload":{"state":"SEARCHING"}}
```

```json
{"type":"ERROR","payload":{"code":"SERVER_NOT_CONFIGURED","message":"..."}}
```

## State machine

```text
IDLE → SEARCHING → NO_RESULT
                 → MATCHES_READY → WAITING_FOR_SELECTION
                                    → LOADING_CONTEXT → CANDIDATE_CONFIRMED
Any state → ERROR
```

`CandidateGateway` never selects the first result. It accepts a selection only while in `WAITING_FOR_SELECTION`, and only if the submitted `candidateId` occurs in the last match list.

## Mock demo

From `huiyi-interviewer/glasses`:

```text
npm test
```

The demo simulates search for two candidates named 张三, explicitly selects `candidateId=202`, and asserts that no request is made for `candidateId=101`.

## Vendor hand-off

To connect real hardware, provide the glasses vendor/model, SDK, transport protocol, Android/iOS support, pairing flow, permission model, message-size limits and reconnect semantics. Implement the `IGlassesBridge` contract behind `VendorGlassesBridge`; do not move phone gateway or Java business logic into vendor code.
