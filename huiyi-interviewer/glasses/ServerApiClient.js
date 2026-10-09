import { getServerBaseUrl, normalizeServerBaseUrl } from "./config/serverConfig.js";

export class ServerApiError extends Error {
  constructor(code, message, details = null) {
    super(message || code);
    this.name = "ServerApiError";
    this.code = code;
    this.details = details;
  }
}

/** Java-only client for the phone gateway. It never reads the database or calls Python. */
export class ServerApiClient {
  constructor({ serverBaseUrl, timeoutMs = 8000, requestAdapter } = {}) {
    this.serverBaseUrl = normalizeServerBaseUrl(serverBaseUrl || getServerBaseUrl());
    this.timeoutMs = timeoutMs;
    this.requestAdapter = requestAdapter;
  }

  async searchCandidates(name) {
    return this.requestJson(`/api/glasses/candidates/search?name=${encodeURIComponent(name || "")}`);
  }

  async getCandidateContext(candidateId) {
    if (!String(candidateId || "").trim()) {
      throw new ServerApiError("INVALID_CANDIDATE_ID", "candidateId is required");
    }
    return this.requestJson(`/api/glasses/candidates/${encodeURIComponent(candidateId)}/context`);
  }

  async healthCheck() {
    return this.requestJson("/api/glasses/health");
  }

  async requestJson(path) {
    if (!this.serverBaseUrl) {
      throw new ServerApiError("SERVER_NOT_CONFIGURED", "AI_INTERVIEWER_SERVER_BASE_URL is not configured");
    }

    const response = await this.performRequest({
      url: `${this.serverBaseUrl}${path}`,
      method: "GET",
      timeout: this.timeoutMs
    });
    const statusCode = Number(response && response.statusCode);
    if (!Number.isFinite(statusCode) || statusCode < 200 || statusCode >= 300) {
      const code = statusCode >= 500 ? "HTTP_5XX" : statusCode >= 400 ? "HTTP_4XX" : "NETWORK_ERROR";
      throw new ServerApiError(code, `Java Server request failed${statusCode ? ` (${statusCode})` : ""}`, response);
    }

    const body = parseBody(response.data);
    if (!body || typeof body !== "object" || typeof body.success !== "boolean") {
      throw new ServerApiError("INVALID_RESPONSE", "Java Server returned an invalid response", body);
    }
    if (!body.success) {
      throw new ServerApiError(body.msg || "SERVER_ERROR", body.msg || "Java Server rejected the request", body);
    }
    return body.data;
  }

  async performRequest(options) {
    try {
      if (this.requestAdapter) {
        return await this.requestAdapter(options);
      }
      if (typeof uni === "undefined" || typeof uni.request !== "function") {
        throw new ServerApiError("SERVER_CLIENT_UNAVAILABLE", "uni.request is unavailable");
      }
      return await new Promise((resolve, reject) => {
        uni.request({
          ...options,
          success: resolve,
          fail: (error) => reject(new ServerApiError("NETWORK_ERROR", "Java Server is unreachable", error))
        });
      });
    } catch (error) {
      if (error instanceof ServerApiError) {
        throw error;
      }
      throw new ServerApiError("NETWORK_ERROR", "Java Server request failed", error);
    }
  }
}

function parseBody(value) {
  if (typeof value !== "string") {
    return value;
  }
  try {
    return JSON.parse(value);
  } catch (_) {
    return null;
  }
}
