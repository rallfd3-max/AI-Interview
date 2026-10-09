package com.itzixi.glasses.websocket;

import com.itzixi.glasses.protocol.GlassesProtocolService;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;
import org.springframework.web.socket.handler.TextWebSocketHandler;

/** WebSocket transport adapter for the phone protocol. */
@Component
public class GlassesWebSocketHandler extends TextWebSocketHandler {

    private final GlassesProtocolService protocolService;

    public GlassesWebSocketHandler(GlassesProtocolService protocolService) {
        this.protocolService = protocolService;
    }

    @Override
    protected void handleTextMessage(WebSocketSession session, TextMessage message) throws Exception {
        String deviceId = (String) session.getAttributes().get(DeviceIdHandshakeInterceptor.DEVICE_ID_ATTRIBUTE);
        protocolService.process(message.getPayload(), deviceId)
                .ifPresent(response -> sendIfOpen(session, response));
    }

    private void sendIfOpen(WebSocketSession session, String payload) {
        try {
            if (session.isOpen()) {
                synchronized (session) {
                    session.sendMessage(new TextMessage(payload));
                }
            }
        } catch (Exception ignored) {
            // Connection loss is handled by the phone client's specified reconnect policy.
        }
    }
}
