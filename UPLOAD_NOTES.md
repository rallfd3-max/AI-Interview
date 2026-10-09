# Project snapshot

This snapshot contains the current project source, tests, documentation, SQL scripts, and application resources.

Local databases, MinIO object storage, logs, dependency caches, virtual environments, compiled outputs, executables, archives, and private environment files are excluded. Install dependencies and service executables separately. The original local working directory is unchanged.

Before running, configure SERVICE_PASSWORD (database and Redis configurations), MINIO_ACCESS_KEY, MINIO_SECRET_KEY, BAIDU_API_KEY, BAIDU_SECRET_KEY, VLLM_API_KEY, and the variables documented in each .env.example. Replace YOUR_API_KEY placeholders in legacy examples with your own credentials.
