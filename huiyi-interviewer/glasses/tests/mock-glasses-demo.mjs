import assert from "node:assert/strict";
import { CandidateGateway, CandidateGatewayState } from "../CandidateGateway.js";
import { MockGlassesBridge } from "../MockGlassesBridge.js";
import { ServerApiClient, ServerApiError } from "../ServerApiClient.js";

const requests = [];
const client = new ServerApiClient({
  serverBaseUrl: "https://java-server.example",
  requestAdapter: async ({ url }) => {
    requests.push(url);
    if (url.includes("/search")) {
      return {
        statusCode: 200,
        data: { success: true, data: { queryName: "张三", matchedCount: 2, candidates: [
          { candidateId: "101", realName: "张三", mobileMasked: "138****0001", school: "第一大学" },
          { candidateId: "202", realName: "张三", mobileMasked: "139****0002", school: "第二大学" }
        ] } }
      };
    }
    if (url.endsWith("/202/context")) {
      return { statusCode: 200, data: { success: true, data: { candidateId: "202", realName: "张三", jobName: "测试工程师" } } };
    }
    return { statusCode: 404, data: { success: false } };
  }
});

const bridge = new MockGlassesBridge();
const gateway = new CandidateGateway({ glassesBridge: bridge, serverApiClient: client });
gateway.start();
await bridge.simulateCandidateSearch(" 张三 ");
const matchesMessage = bridge.lastMessage("CANDIDATE_MATCHES");
assert.equal(matchesMessage.payload.count, 2);
assert.deepEqual(matchesMessage.payload.candidates.map((candidate) => candidate.candidateId), ["101", "202"]);
assert.equal(gateway.currentCandidateId, null, "No candidate may be auto-selected");

await bridge.simulateCandidateSelection("202");
assert.equal(gateway.state, CandidateGatewayState.CANDIDATE_CONFIRMED);
assert.equal(gateway.currentCandidateId, "202");
assert.equal(bridge.lastMessage("CANDIDATE_CONTEXT").payload.candidateId, "202");
assert.ok(requests.some((url) => url.endsWith("/202/context")));
assert.ok(!requests.some((url) => url.endsWith("/101/context")), "The first same-name candidate must never be loaded by default");

const unconfigured = new ServerApiClient({ requestAdapter: async () => ({ statusCode: 200, data: {} }) });
await assert.rejects(() => unconfigured.searchCandidates("张三"), (error) => error instanceof ServerApiError && error.code === "SERVER_NOT_CONFIGURED");

const badJsonClient = new ServerApiClient({
  serverBaseUrl: "https://java-server.example",
  requestAdapter: async () => ({ statusCode: 200, data: "not-json" })
});
await assert.rejects(() => badJsonClient.searchCandidates("张三"), (error) => error.code === "INVALID_RESPONSE");

const httpFailureClient = new ServerApiClient({
  serverBaseUrl: "https://java-server.example",
  requestAdapter: async () => ({ statusCode: 503, data: {} })
});
await assert.rejects(() => httpFailureClient.searchCandidates("张三"), (error) => error.code === "HTTP_5XX");

bridge.disconnect();
await bridge.simulateCandidateSelection("202");
assert.equal(gateway.state, CandidateGatewayState.ERROR);

console.log("Mock smart-glasses flow verified: duplicate candidates require explicit selection and candidateId=202 is used.");
