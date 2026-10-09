# Smart Glasses Repository Audit

Audit date: 2026-08-28. This document records the repository state used for the smart-glasses candidate lookup iteration.

## Actual modules and entry points

| Area | Actual location | Entry / build observation |
|---|---|---|
| Java business server | `ai-interviewer-master` | Spring Boot entry: `api/src/main/java/com/itzixi/Application.java`; Maven multi-module project |
| Candidate business code | `api/.../CandidateController.java`, `service/.../CandidateServiceImpl.java`, `dao/.../CandidateMapperCustom.xml` | Existing candidate search is implemented here |
| Candidate mobile client | `huiyi-interviewer` | uni-app/Vue 2 project; `App.vue` and `main.js` are present |
| Management UI | `ai-interviewer-fronted-master` | Legacy static/multi-page Vue 2 structure, not a complete Vue CLI source tree |
| AI/review server | `ai-interviewer-digital-dev` | FastAPI entry: `interviewer_dpsk_server_v2.py` |
| Smart-glasses UI/SDK | Not found as an identifiable project or vendor SDK | No UI was changed; a non-UI gateway module was added to the existing uni-app project |

## Existing candidate identity behavior

The repository already has `GET /candidate/match?name=`. Its implementation:

- validates a nonblank name in `CandidateController`;
- trims the name in `CandidateServiceImpl`;
- delegates to `CandidateMapperCustom.findAllByRealName`;
- performs exact `TRIM(c.real_name)` matching;
- returns every same-name candidate in `CandidateMatchResultVO`;
- returns masked mobile numbers in `CandidateMatchVO`.

The smart-glasses work does not add a second name-query mapper or SQL statement. It delegates to `CandidateService.matchByRealName`. `candidateId`, selected by a human from the returned list, is the only identifier used for the new context request.

## Configuration findings

Existing projects contain several historical hard-coded localhost, LAN and overlay-network addresses. The new gateway does not reuse them. Its only server configuration key is `AI_INTERVIEWER_SERVER_BASE_URL`, documented in `huiyi-interviewer/.env.example`. An empty value produces `SERVER_NOT_CONFIGURED`; there is no localhost fallback.

Existing Java and mobile configuration still contains secrets, addresses and legacy direct Python calls outside this feature. They were recorded but not broadly refactored to keep this iteration minimal and reversible.

## Build and test findings before this change

- Java modules previously built with `mvn -DskipTests package`; there was no focused regression coverage for this feature.
- The management UI's `npm run build` fails before this change because `./src/main.js` is absent. It is a pre-existing project-structure mismatch.
- Python files parse syntactically, but the Python service has no committed dependency lock/requirements file.
- Existing `MyGLMTestV3` and `MyGLMTestV4` invoke an external paid model API. They are excluded from normal unit-test execution so a local unit test run never silently calls an external service.

## Files changed by this iteration

- Java smart-glasses Controller, context service and safe context VO.
- Java unit tests and test dependency/Surefire configuration.
- `huiyi-interviewer/glasses/`: Java-only Server API client, stateful candidate gateway, mock bridge and vendor extension point.
- `huiyi-interviewer/.env.example`.
- Smart-glasses integration, API, test and final reports under `docs/`.

## Risks retained for follow-up

1. Real glasses model, SDK, transport and permission model have not been supplied.
2. The new Java endpoint has no dedicated authentication layer yet; it follows the legacy server's current authentication boundary. Add authorization before non-demo deployment.
3. Full endpoint/database integration was not executed because a clean, controlled MySQL test fixture is not present in the repository.
4. Existing hard-coded secrets, data files, runtime artifacts and legacy direct Python client calls remain outside this narrowly scoped change.
