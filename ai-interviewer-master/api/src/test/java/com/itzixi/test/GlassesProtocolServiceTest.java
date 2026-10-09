package com.itzixi.test;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.itzixi.glasses.protocol.FaceCandidateResolver;
import com.itzixi.glasses.protocol.GlassesProtocolService;
import com.itzixi.pojo.vo.GlassesCandidateContextVO;
import com.itzixi.service.GlassesCandidateContextService;
import org.junit.jupiter.api.Test;

import java.nio.charset.StandardCharsets;
import java.util.Base64;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class GlassesProtocolServiceTest {

    private final ObjectMapper objectMapper = new ObjectMapper();
    private final FaceCandidateResolver resolver = mock(FaceCandidateResolver.class);
    private final GlassesCandidateContextService contextService = mock(GlassesCandidateContextService.class);
    private final GlassesProtocolService service = new GlassesProtocolService(objectMapper, resolver, contextService);

    @Test
    void repliesToPingAndPersonLeft() throws Exception {
        assertEquals("pong", json(service.process("{\"type\":\"ping\"}", "glasses-001").orElseThrow()).path("type").asText());
        JsonNode clear = json(service.process("{\"type\":\"event\",\"event\":\"person_left\"}", "glasses-001").orElseThrow());
        assertEquals("clear", clear.path("type").asText());
        assertEquals("person_left", clear.path("reason").asText());
    }

    @Test
    void convertsResolvedCandidateToSafePersonCard() throws Exception {
        String image = Base64.getEncoder().encodeToString("jpeg".getBytes(StandardCharsets.UTF_8));
        when(resolver.resolveCandidateId(any(), eq("glasses-001"))).thenReturn(Optional.of("202"));
        GlassesCandidateContextVO context = new GlassesCandidateContextVO();
        context.setCandidateId("202");
        context.setRealName("张三");
        context.setJobName("Java 开发工程师");
        context.setInterviewStatus("COMPLETED");
        when(contextService.getContext("202")).thenReturn(Optional.of(context));

        JsonNode response = json(service.process("{\"type\":\"face\",\"img\":\"" + image + "\"}", "glasses-001").orElseThrow());

        assertEquals("person_info", response.path("type").asText());
        assertEquals("202", response.path("id").asText());
        assertEquals("张三", response.path("name").asText());
        assertEquals("Java 开发工程师", response.path("role").asText());
        assertTrue(response.path("display_lines").size() <= 5);
        verify(contextService).getContext("202");
    }

    @Test
    void returnsProtocolErrorsForUnknownOrInvalidFace() throws Exception {
        String image = Base64.getEncoder().encodeToString("jpeg".getBytes(StandardCharsets.UTF_8));
        when(resolver.resolveCandidateId(any(), eq("glasses-001"))).thenReturn(Optional.empty());

        JsonNode unknown = json(service.process("{\"type\":\"face\",\"img\":\"" + image + "\"}", "glasses-001").orElseThrow());
        JsonNode invalid = json(service.process("{\"type\":\"face\",\"img\":\"not-base64!\"}", "glasses-001").orElseThrow());

        assertEquals("unknown_face", unknown.path("code").asText());
        assertEquals("bad_image", invalid.path("code").asText());
    }

    @Test
    void leavesAudioAndMalformedFramesWithoutReply() {
        assertTrue(service.process("{\"type\":\"audio\",\"data\":\"abc\"}", "glasses-001").isEmpty());
        assertTrue(service.process("not-json", "glasses-001").isEmpty());
        assertFalse(service.process("{\"type\":\"event\",\"event\":\"other\"}", "glasses-001").isPresent());
    }

    private JsonNode json(String value) throws Exception {
        return objectMapper.readTree(value);
    }
}
