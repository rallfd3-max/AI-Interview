/**
 * Device adapter contract. Vendor integrations must implement this contract and
 * must not put database or Java Server calls into the glasses adapter.
 */
export class IGlassesBridge {
  connect() { throw new Error("Not implemented"); }
  disconnect() { throw new Error("Not implemented"); }
  isConnected() { throw new Error("Not implemented"); }
  onCandidateSearch(_) { throw new Error("Not implemented"); }
  onCandidateSelected(_) { throw new Error("Not implemented"); }
  sendCandidateMatches(_) { throw new Error("Not implemented"); }
  sendCandidateContext(_) { throw new Error("Not implemented"); }
  sendLoading(_) { throw new Error("Not implemented"); }
  sendError(_) { throw new Error("Not implemented"); }
  sendConnectionState(_) { throw new Error("Not implemented"); }
}
