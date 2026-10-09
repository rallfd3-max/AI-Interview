package com.itzixi.glasses.protocol;

import java.util.List;

/** Metadata passed to a real face-recognition adapter. The image is never logged. */
public record FaceRecognitionRequest(
        String jpegBase64,
        long capturedAt,
        int faceCount,
        List<Integer> faceBox
) {
}
