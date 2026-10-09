export const CandidateGatewayState = Object.freeze({
  IDLE: "IDLE",
  SEARCHING: "SEARCHING",
  NO_RESULT: "NO_RESULT",
  MATCHES_READY: "MATCHES_READY",
  WAITING_FOR_SELECTION: "WAITING_FOR_SELECTION",
  LOADING_CONTEXT: "LOADING_CONTEXT",
  CANDIDATE_CONFIRMED: "CANDIDATE_CONFIRMED",
  ERROR: "ERROR"
});

/** Coordinates glasses events with the Java-only ServerApiClient. */
export class CandidateGateway {
  constructor({ glassesBridge, serverApiClient }) {
    this.glassesBridge = glassesBridge;
    this.serverApiClient = serverApiClient;
    this.state = CandidateGatewayState.IDLE;
    this.matches = [];
    this.currentCandidateId = null;
    this.glassesBridge.onCandidateSearch((event) => this.handleSearch(event && event.payload && event.payload.name));
    this.glassesBridge.onCandidateSelected((event) => this.handleSelection(event && event.payload && event.payload.candidateId));
  }

  start() {
    this.glassesBridge.connect();
    this.state = CandidateGatewayState.IDLE;
  }

  async handleSearch(name) {
    if (!this.glassesBridge.isConnected()) {
      return this.fail("GLASSES_DISCONNECTED", "Glasses are disconnected");
    }
    this.state = CandidateGatewayState.SEARCHING;
    this.safeSend("sendLoading", { state: this.state });
    try {
      const result = await this.serverApiClient.searchCandidates(name);
      const candidates = Array.isArray(result && result.candidates) ? result.candidates : [];
      this.matches = candidates;
      this.currentCandidateId = null;
      if (!candidates.length) {
        this.state = CandidateGatewayState.NO_RESULT;
        this.safeSend("sendError", { code: "NO_RESULT", message: "No candidate matched this name" });
        return;
      }
      this.state = CandidateGatewayState.MATCHES_READY;
      this.safeSend("sendCandidateMatches", {
        queryName: result.queryName,
        count: result.matchedCount == null ? candidates.length : result.matchedCount,
        candidates
      });
      // Even one result requires explicit human selection. Never auto-select index 0.
      this.state = CandidateGatewayState.WAITING_FOR_SELECTION;
    } catch (error) {
      this.fail(error.code || "NETWORK_ERROR", error.message || "Candidate search failed");
    }
  }

  async handleSelection(candidateId) {
    if (!this.glassesBridge.isConnected()) {
      return this.fail("GLASSES_DISCONNECTED", "Glasses are disconnected");
    }
    const normalizedId = String(candidateId || "").trim();
    if (this.state !== CandidateGatewayState.WAITING_FOR_SELECTION) {
      return this.fail("INVALID_SELECTION_STATE", "Search and review matches before selecting a candidate");
    }
    if (!this.matches.some((candidate) => String(candidate.candidateId) === normalizedId)) {
      return this.fail("CANDIDATE_NOT_IN_MATCHES", "Selected candidate was not returned by the latest search");
    }

    this.state = CandidateGatewayState.LOADING_CONTEXT;
    this.safeSend("sendLoading", { state: this.state, candidateId: normalizedId });
    try {
      const context = await this.serverApiClient.getCandidateContext(normalizedId);
      if (!context || String(context.candidateId) !== normalizedId) {
        return this.fail("INVALID_RESPONSE", "Context does not match the selected candidate");
      }
      this.currentCandidateId = normalizedId;
      this.state = CandidateGatewayState.CANDIDATE_CONFIRMED;
      this.safeSend("sendCandidateContext", context);
    } catch (error) {
      this.fail(error.code || "NETWORK_ERROR", error.message || "Candidate context request failed");
    }
  }

  fail(code, message) {
    this.state = CandidateGatewayState.ERROR;
    this.safeSend("sendError", { code, message });
  }

  safeSend(method, payload) {
    if (this.glassesBridge.isConnected()) {
      this.glassesBridge[method](payload);
    }
  }
}
