import { IGlassesBridge } from "./IGlassesBridge.js";

/** In-memory bridge used by the runnable demo and automated tests. */
export class MockGlassesBridge extends IGlassesBridge {
  constructor() {
    super();
    this.connected = false;
    this.searchHandler = null;
    this.selectHandler = null;
    this.messages = [];
  }

  connect() {
    this.connected = true;
    this.sendConnectionState({ connected: true });
  }

  disconnect() {
    this.connected = false;
    this.sendConnectionState({ connected: false });
  }

  isConnected() { return this.connected; }
  onCandidateSearch(handler) { this.searchHandler = handler; }
  onCandidateSelected(handler) { this.selectHandler = handler; }
  sendCandidateMatches(payload) { this.record("CANDIDATE_MATCHES", payload); }
  sendCandidateContext(payload) { this.record("CANDIDATE_CONTEXT", payload); }
  sendLoading(payload) { this.record("LOADING", payload); }
  sendError(payload) { this.record("ERROR", payload); }
  sendConnectionState(payload) { this.record("CONNECTION_STATE", payload); }

  async simulateCandidateSearch(name) {
    if (this.searchHandler) {
      return this.searchHandler({ type: "SEARCH_CANDIDATE", payload: { name } });
    }
  }

  async simulateCandidateSelection(candidateId) {
    if (this.selectHandler) {
      return this.selectHandler({ type: "SELECT_CANDIDATE", payload: { candidateId } });
    }
  }

  record(type, payload) {
    this.messages.push({ type, payload });
  }

  lastMessage(type) {
    return [...this.messages].reverse().find((message) => message.type === type);
  }
}
