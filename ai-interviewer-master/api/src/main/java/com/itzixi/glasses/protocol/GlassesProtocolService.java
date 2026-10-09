package com.itzixi.glasses.protocol;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.itzixi.pojo.vo.GlassesCandidateContextVO;
import com.itzixi.service.GlassesCandidateContextService;
import org.apache.commons.lang3.StringUtils;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.Base64;
import java.util.List;
import java.util.Optional;

/** Implements the mobile WebSocket contract without logging face or audio payloads. */
@Service
public class GlassesProtocolService {

    private static final int MAX_IMAGE_BYTES = 1024 * 1024;
    private static final int MAX_DISPLAY_LINES = 5;
    private static final int MAX_DISPLAY_LINE_LENGTH = 18;

    private final ObjectMapper objectMapper;
    private final FaceCandidateResolver faceCandidateResolver;
    private final GlassesCandidateContextService candidateContextService;

    public GlassesProtocolService(ObjectMapper objectMapper,
                                  FaceCandidateResolver faceCandidateResolver,
                                  GlassesCandidateContextService candidateContextService) {
        this.objectMapper = objectMapper;
        this.faceCandidateResolver = faceCandidateResolver;
        this.candidateContextService = candidateContextService;
    }

    /**
     * Processes one UTF-8 JSON text frame. An empty result means that the protocol
     * intentionally does not require a response (audio/unknown/malformed frames).
     */
    public Optional<String> process(String rawMessage, String deviceId) {
        try {
            JsonNode message = objectMapper.readTree(rawMessage);
            if (message == null || !message.isObject()) {
                return Optional.empty();
            }
            String type = message.path("type").asText("");
            return switch (type) {
                case "ping" -> Optional.of(toJson(objectMapper.createObjectNode().put("type", "pong")));
                case "face" -> processFace(message, deviceId);
                case "audio" -> Optional.empty();
                case "event" -> processEvent(message);
                default -> Optional.empty();
            };
        } catch (JsonProcessingException ignored) {
            // The mobile contract requires malformed frames to be silently discarded.
            return Optional.empty();
        } catch (RuntimeException ignored) {
            return Optional.of(error("internal", "Unable to process message"));
        }
    }

    private Optional<String> processFace(JsonNode message, String deviceId) {
        String image = message.path("img").asText("");
        if (!isValidImage(image)) {
            return Optional.of(error("bad_image", "Invalid face image"));
        }
        FaceRecognitionRequest request = new FaceRecognitionRequest(
                image,
                message.path("ts").asLong(System.currentTimeMillis()),
                message.path("face_count").asInt(0),
                readFaceBox(message.path("face_box"))
        );
        Optional<String> candidateId = faceCandidateResolver.resolveCandidateId(request, deviceId);
        if (candidateId.isEmpty()) {
            return Optional.of(error("unknown_face", "No enrolled candidate matched this face"));
        }
        Optional<GlassesCandidateContextVO> context = candidateContextService.getContext(candidateId.get());
        if (context.isEmpty()) {
            return Optional.of(error("unknown_face", "Matched candidate is unavailable"));
        }
        return Optional.of(personInfo(context.get()));
    }

    private Optional<String> processEvent(JsonNode message) {
        if (!"person_left".equals(message.path("event").asText())) {
            return Optional.empty();
        }
        ObjectNode clear = objectMapper.createObjectNode();
        clear.put("type", "clear");
        clear.put("reason", "person_left");
        clear.put("ts", System.currentTimeMillis());
        return Optional.of(toJson(clear));
    }

    private String personInfo(GlassesCandidateContextVO context) {
        ObjectNode person = objectMapper.createObjectNode();
        person.put("type", "person_info");
        person.put("id", context.getCandidateId());
        person.put("name", context.getRealName());
        putIfNotBlank(person, "role", context.getJobName());
        putIfNotBlank(person, "notes", context.getLatestInterviewSummary());
        ArrayNode lines = person.putArray("display_lines");
        for (String line : displayLines(context)) {
            lines.add(line);
        }
        person.put("ts", System.currentTimeMillis());
        return toJson(person);
    }

    private List<String> displayLines(GlassesCandidateContextVO context) {
        // ArrayList accepts absent optional fields. List.of would throw on null and
        // incorrectly turn an otherwise valid card into an internal protocol error.
        List<String> candidates = new ArrayList<>();
        candidates.add(context.getRealName());
        candidates.add(context.getJobName());
        candidates.add(joinNonBlank(context.getSchool(), context.getMajor()));
        candidates.add(StringUtils.isBlank(context.getInterviewStatus()) ? null : "面试:" + context.getInterviewStatus());
        candidates.add(StringUtils.isBlank(context.getLatestInterviewSummary()) ? null : "备注:" + context.getLatestInterviewSummary());
        List<String> lines = new ArrayList<>();
        for (String line : candidates) {
            if (StringUtils.isNotBlank(line) && lines.size() < MAX_DISPLAY_LINES) {
                lines.add(StringUtils.abbreviate(StringUtils.normalizeSpace(line), MAX_DISPLAY_LINE_LENGTH));
            }
        }
        return lines;
    }

    private String joinNonBlank(String first, String second) {
        if (StringUtils.isBlank(first)) {
            return second;
        }
        if (StringUtils.isBlank(second)) {
            return first;
        }
        return first + " / " + second;
    }

    private boolean isValidImage(String encodedImage) {
        if (StringUtils.isBlank(encodedImage)) {
            return false;
        }
        try {
            return Base64.getDecoder().decode(encodedImage).length <= MAX_IMAGE_BYTES;
        } catch (IllegalArgumentException ignored) {
            return false;
        }
    }

    private List<Integer> readFaceBox(JsonNode node) {
        List<Integer> values = new ArrayList<>();
        if (node.isArray() && node.size() == 4) {
            for (JsonNode item : node) {
                values.add(item.asInt());
            }
        }
        return values;
    }

    private String error(String code, String message) {
        ObjectNode error = objectMapper.createObjectNode();
        error.put("type", "error");
        error.put("code", code);
        error.put("msg", message);
        error.put("ts", System.currentTimeMillis());
        return toJson(error);
    }

    private void putIfNotBlank(ObjectNode node, String field, String value) {
        if (StringUtils.isNotBlank(value)) {
            node.put(field, value);
        }
    }

    private String toJson(ObjectNode node) {
        try {
            return objectMapper.writeValueAsString(node);
        } catch (JsonProcessingException exception) {
            throw new IllegalStateException("Unable to serialize WebSocket response", exception);
        }
    }
}
