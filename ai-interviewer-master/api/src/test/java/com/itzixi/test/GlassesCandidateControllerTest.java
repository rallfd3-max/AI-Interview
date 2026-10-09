package com.itzixi.test;

import com.itzixi.controller.GlassesCandidateController;
import com.itzixi.grace.result.GraceJSONResult;
import com.itzixi.pojo.vo.CandidateMatchResultVO;
import com.itzixi.pojo.vo.GlassesCandidateContextVO;
import com.itzixi.service.CandidateService;
import com.itzixi.service.GlassesCandidateContextService;
import org.junit.jupiter.api.Test;
import org.springframework.test.util.ReflectionTestUtils;

import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class GlassesCandidateControllerTest {

    private final CandidateService candidateService = mock(CandidateService.class);
    private final GlassesCandidateContextService contextService = mock(GlassesCandidateContextService.class);
    private final GlassesCandidateController controller = configuredController();

    @Test
    void delegatesSearchToExistingCandidateService() {
        CandidateMatchResultVO matches = new CandidateMatchResultVO("张三", 2, List.of());
        when(candidateService.matchByRealName(" 张三 ")).thenReturn(matches);

        GraceJSONResult result = controller.search(" 张三 ");

        assertTrue(result.getSuccess());
        assertEquals(matches, result.getData());
        verify(candidateService).matchByRealName(" 张三 ");
    }

    @Test
    void rejectsEmptyNameAndInvalidCandidateId() {
        GraceJSONResult nameResult = controller.search(" ");
        GraceJSONResult idResult = controller.context(" ");

        assertFalse(nameResult.getSuccess());
        assertEquals("NAME_REQUIRED", nameResult.getMsg());
        assertFalse(idResult.getSuccess());
        assertEquals("INVALID_CANDIDATE_ID", idResult.getMsg());
    }

    @Test
    void returnsOnlyContextForSelectedCandidateId() {
        GlassesCandidateContextVO context = new GlassesCandidateContextVO();
        context.setCandidateId("202");
        context.setRealName("张三");
        when(contextService.getContext("202")).thenReturn(Optional.of(context));

        GraceJSONResult result = controller.context("202");

        assertTrue(result.getSuccess());
        assertEquals(context, result.getData());
        verify(contextService).getContext("202");
    }

    @Test
    void returnsCandidateNotFoundForUnknownId() {
        when(contextService.getContext("404")).thenReturn(Optional.empty());

        GraceJSONResult result = controller.context("404");

        assertFalse(result.getSuccess());
        assertEquals("CANDIDATE_NOT_FOUND", result.getMsg());
    }

    private GlassesCandidateController configuredController() {
        GlassesCandidateController target = new GlassesCandidateController();
        ReflectionTestUtils.setField(target, "candidateService", candidateService);
        ReflectionTestUtils.setField(target, "glassesCandidateContextService", contextService);
        return target;
    }
}
