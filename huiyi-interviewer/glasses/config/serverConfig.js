const SERVER_BASE_URL_KEY = "AI_INTERVIEWER_SERVER_BASE_URL";

export function getServerBaseUrl() {
  let configuredUrl = "";
  if (typeof process !== "undefined" && process.env) {
    configuredUrl = process.env[SERVER_BASE_URL_KEY] || "";
  }
  if (!configuredUrl && typeof uni !== "undefined" && typeof uni.getStorageSync === "function") {
    configuredUrl = uni.getStorageSync(SERVER_BASE_URL_KEY) || "";
  }
  return normalizeServerBaseUrl(configuredUrl);
}

export function setServerBaseUrl(serverBaseUrl) {
  const normalized = normalizeServerBaseUrl(serverBaseUrl);
  if (typeof uni !== "undefined" && typeof uni.setStorageSync === "function") {
    uni.setStorageSync(SERVER_BASE_URL_KEY, normalized);
  }
  return normalized;
}

export function normalizeServerBaseUrl(serverBaseUrl) {
  return String(serverBaseUrl || "").trim().replace(/\/+$/, "");
}

export { SERVER_BASE_URL_KEY };
