# AI-Interviewer

## Smart-glasses candidate lookup

The smart-glasses phone gateway is implemented in [`huiyi-interviewer/glasses`](./huiyi-interviewer/glasses). It uses the Java server only, requires an explicit candidate selection, and uses `candidateId` after a name search.

Set `AI_INTERVIEWER_SERVER_BASE_URL` using [`huiyi-interviewer/.env.example`](./huiyi-interviewer/.env.example). Keep it blank until a server is assigned; the gateway returns `SERVER_NOT_CONFIGURED` rather than guessing an address.

Documentation:

- [`docs/CODEX_REPO_AUDIT.md`](./docs/CODEX_REPO_AUDIT.md)
- [`docs/SMART_GLASSES_INTEGRATION.md`](./docs/SMART_GLASSES_INTEGRATION.md)
- [`docs/SMART_GLASSES_API.md`](./docs/SMART_GLASSES_API.md)
- [`docs/SMART_GLASSES_TEST_REPORT.md`](./docs/SMART_GLASSES_TEST_REPORT.md)
- [`docs/CODEX_FINAL_REPORT.md`](./docs/CODEX_FINAL_REPORT.md)
