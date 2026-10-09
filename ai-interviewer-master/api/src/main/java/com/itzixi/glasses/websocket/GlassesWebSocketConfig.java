package com.itzixi.glasses.websocket;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.socket.config.annotation.EnableWebSocket;
import org.springframework.web.socket.config.annotation.WebSocketConfigurer;
import org.springframework.web.socket.config.annotation.WebSocketHandlerRegistry;
import org.springframework.web.socket.server.standard.ServletServerContainerFactoryBean;

/** Registers the mobile contract at the Java server's configured HTTP(S) port. */
@Configuration
@EnableWebSocket
public class GlassesWebSocketConfig implements WebSocketConfigurer {

    private final GlassesWebSocketHandler handler;
    private final DeviceIdHandshakeInterceptor deviceIdHandshakeInterceptor;
    private final String path;

    public GlassesWebSocketConfig(GlassesWebSocketHandler handler,
                                  DeviceIdHandshakeInterceptor deviceIdHandshakeInterceptor,
                                  @Value("${smart-glasses.websocket.path:/ws}") String path) {
        this.handler = handler;
        this.deviceIdHandshakeInterceptor = deviceIdHandshakeInterceptor;
        this.path = path;
    }

    @Override
    public void registerWebSocketHandlers(WebSocketHandlerRegistry registry) {
        registry.addHandler(handler, path)
                .addInterceptors(deviceIdHandshakeInterceptor);
    }

    @Bean
    public ServletServerContainerFactoryBean smartGlassesWebSocketContainer(
            @Value("${smart-glasses.websocket.max-text-message-size:262144}") int maxTextMessageSize) {
        ServletServerContainerFactoryBean container = new ServletServerContainerFactoryBean();
        container.setMaxTextMessageBufferSize(maxTextMessageSize);
        return container;
    }
}
