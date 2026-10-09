package com.itzixi.glasses.protocol;

import java.util.Optional;

/**
 * Hardware/AI extension point that maps a face image to an existing candidateId.
 * Implementations must return the stable database candidateId, never a name.
 */
public interface FaceCandidateResolver {

    Optional<String> resolveCandidateId(FaceRecognitionRequest request, String deviceId);
}
