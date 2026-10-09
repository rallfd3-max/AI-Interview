package com.itzixi.controller;

import com.itzixi.grace.result.GraceJSONResult;
import com.itzixi.pojo.vo.GlassesCandidateContextVO;
import com.itzixi.service.CandidateService;
import com.itzixi.service.GlassesCandidateContextService;
import jakarta.annotation.Resource;
import org.apache.commons.lang3.StringUtils;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.Optional;

/**
 * Java-only server boundary for the smart-glasses phone gateway.
 */
@RestController
@RequestMapping("api/glasses")
public class GlassesCandidateController {

    @Resource
    private CandidateService candidateService;

    @Resource
    private GlassesCandidateContextService glassesCandidateContextService;

    /** Reuses the existing name matching service and never implements another query. */
    @GetMapping("candidates/search")
    public GraceJSONResult search(@RequestParam String name) {
        if (StringUtils.isBlank(name)) {
            return GraceJSONResult.errorMsg("NAME_REQUIRED");
        }
        return GraceJSONResult.ok(candidateService.matchByRealName(name));
    }

    /** Returns only the minimum candidate context needed by the glasses display. */
    @GetMapping("candidates/{candidateId}/context")
    public GraceJSONResult context(@PathVariable String candidateId) {
        if (StringUtils.isBlank(candidateId) || candidateId.length() > 64) {
            return GraceJSONResult.errorMsg("INVALID_CANDIDATE_ID");
        }
        Optional<GlassesCandidateContextVO> context = glassesCandidateContextService.getContext(candidateId);
        return context.<GraceJSONResult>map(GraceJSONResult::ok)
                .orElseGet(() -> GraceJSONResult.errorMsg("CANDIDATE_NOT_FOUND"));
    }

    @GetMapping("health")
    public GraceJSONResult health() {
        return GraceJSONResult.ok("SMART_GLASSES_GATEWAY_READY");
    }
}
