package com.itzixi.glasses.protocol;

import org.springframework.stereotype.Component;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;

import java.util.Optional;

/**
 * Safe default until a real face-recognition SDK/service is configured.
 * It intentionally does not guess an identity from a name or image.
 */
@Component
@ConditionalOnProperty(name = "smart-glasses.face.default-resolver-enabled", havingValue = "true", matchIfMissing = true)
public class UnknownFaceCandidateResolver implements FaceCandidateResolver {

    @Override
    public Optional<String> resolveCandidateId(FaceRecognitionRequest request, String deviceId) {
        return Optional.empty();
    }
}
