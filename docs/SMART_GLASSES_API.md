# Smart Glasses Java API

The mobile/glasses WebSocket contract is documented separately in
[SMART_GLASSES_WEBSOCKET_API.md](SMART_GLASSES_WEBSOCKET_API.md). This document
covers the internal REST candidate APIs used by the phone gateway.

Base path: `/api/glasses`

All endpoints return the existing `GraceJSONResult` envelope:

```json
{"status":200,"msg":"success","success":true,"data":{}}
```

The phone gateway must treat `success: false` as an application error even when HTTP is 200.

## Search candidates

`GET /api/glasses/candidates/search?name={name}`

Implementation delegates directly to the existing `CandidateService.matchByRealName(name)`. It does not have its own mapper or SQL.

Success payload:

```json
{
  "queryName":"张三",
  "matchedCount":2,
  "candidates":[
    {
      "candidateId":"101",
      "realName":"张三",
      "mobileMasked":"138****0001",
      "sex":1,
      "email":"candidate@example.com",
      "jobId":"job-1",
      "jobName":"Java开发工程师",
      "school":"第一大学",
      "major":"软件工程"
    }
  ]
}
```

Failure: `NAME_REQUIRED` when `name` is blank.

`email` is inherited from the existing match VO. A production authorization review should decide whether it is necessary for device display; the new context endpoint intentionally does not return it.

## Candidate context

`GET /api/glasses/candidates/{candidateId}/context`

This endpoint is called only after human selection. It aggregates existing Candidate, Job and latest InterviewRecord service data by `candidateId`.

Success payload fields:

| Field | Source / behavior |
|---|---|
| `candidateId`, `realName`, `school`, `major` | Candidate |
| `gender` | Maps existing numeric sex to 男 / 女 / 保密 / UNKNOWN |
| `jobId`, `jobName`, `jobDescriptionSummary` | Candidate + Job |
| `candidateProfile`, `experienceSummary` | Candidate introduction/experience, normalized and limited to 240 characters |
| `interviewStatus` | `NOT_STARTED` or `COMPLETED` based on existing records |
| `latestInterviewSummary`, `latestInterviewScore` | First record from existing latest-first service result |

Explicitly excluded: identity number, mobile number, email, home address, face/media URLs, password, token, storage credentials and model credentials.

Failures:

| Code | Meaning |
|---|---|
| `INVALID_CANDIDATE_ID` | Blank or longer than 64 characters |
| `CANDIDATE_NOT_FOUND` | No candidate exists for the selected identifier |

## Health

`GET /api/glasses/health`

Returns `SMART_GLASSES_GATEWAY_READY` without querying the candidate database. It is intended for the phone gateway's configuration/connectivity check.

## Client-side error codes

The phone `ServerApiClient` reports `SERVER_NOT_CONFIGURED`, `SERVER_CLIENT_UNAVAILABLE`, `NETWORK_ERROR`, `HTTP_4XX`, `HTTP_5XX`, `INVALID_RESPONSE`, or the Java application error message. `CandidateGateway` additionally reports `GLASSES_DISCONNECTED`, `NO_RESULT`, `INVALID_SELECTION_STATE`, and `CANDIDATE_NOT_IN_MATCHES`.
