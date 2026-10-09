import { IGlassesBridge } from "./IGlassesBridge.js";

/**
 * Extension point for the eventual glasses vendor SDK. No SDK calls are made
 * until a vendor, model, protocol and permission model are supplied.
 */
export class VendorGlassesBridge extends IGlassesBridge {
  constructor({ vendorAdapter } = {}) {
    super();
    this.vendorAdapter = vendorAdapter;
  }

  connect() {
    if (!this.vendorAdapter) {
      throw new Error("VENDOR_SDK_NOT_CONFIGURED");
    }
    return this.vendorAdapter.connect();
  }

  disconnect() { return this.requireAdapter().disconnect(); }
  isConnected() { return this.requireAdapter().isConnected(); }
  onCandidateSearch(handler) { return this.requireAdapter().onCandidateSearch(handler); }
  onCandidateSelected(handler) { return this.requireAdapter().onCandidateSelected(handler); }
  sendCandidateMatches(payload) { return this.requireAdapter().sendCandidateMatches(payload); }
  sendCandidateContext(payload) { return this.requireAdapter().sendCandidateContext(payload); }
  sendLoading(payload) { return this.requireAdapter().sendLoading(payload); }
  sendError(payload) { return this.requireAdapter().sendError(payload); }
  sendConnectionState(payload) { return this.requireAdapter().sendConnectionState(payload); }

  requireAdapter() {
    if (!this.vendorAdapter) {
      throw new Error("VENDOR_SDK_NOT_CONFIGURED");
    }
    return this.vendorAdapter;
  }
}
