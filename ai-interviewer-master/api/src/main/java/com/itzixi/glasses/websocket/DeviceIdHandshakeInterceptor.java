package com.itzixi.glasses.websocket;

import org.apache.commons.lang3.StringUtils;
import org.springframework.http.server.ServerHttpRequest;
import org.springframework.http.server.ServerHttpResponse;
import org.springframework.http.server.ServletServerHttpRequest;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.WebSocketHandler;
import org.springframework.web.socket.server.HandshakeInterceptor;

import java.util.Map;

/** Requires and retains the protocol's X-Device-Id handshake header. */
@Component
public class DeviceIdHandshakeInterceptor implements HandshakeInterceptor {

    public static final String DEVICE_ID_ATTRIBUTE = "smart_glasses_device_id";

    @Override
    public boolean beforeHandshake(ServerHttpRequest request, ServerHttpResponse response,
                                   WebSocketHandler wsHandler, Map<String, Object> attributes) {
        String deviceId = request.getHeaders().getFirst("X-Device-Id");
        if (StringUtils.isBlank(deviceId) || deviceId.length() > 128) {
            response.setStatusCode(org.springframework.http.HttpStatus.BAD_REQUEST);
            return false;
        }
        attributes.put(DEVICE_ID_ATTRIBUTE, deviceId.trim());
        return true;
    }

    @Override
    public void afterHandshake(ServerHttpRequest request, ServerHttpResponse response,
                               WebSocketHandler wsHandler, Exception exception) {
        // No PII or device identifiers are logged here.
    }
}
