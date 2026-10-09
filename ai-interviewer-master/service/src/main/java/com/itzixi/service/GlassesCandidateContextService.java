package com.itzixi.service;

import com.itzixi.pojo.vo.GlassesCandidateContextVO;

import java.util.Optional;

/**
 * Read-only candidate context for the smart-glasses gateway.
 * Candidate identity is always the candidateId selected by a human.
 */
public interface GlassesCandidateContextService {

    Optional<GlassesCandidateContextVO> getContext(String candidateId);
}
