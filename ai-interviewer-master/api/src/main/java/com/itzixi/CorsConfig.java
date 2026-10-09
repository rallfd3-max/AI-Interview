package com.itzixi;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

/**
 * @ClassName CorsConfig
 * @Author 公众号【翙邑科技】
 * @Version 1.0
 * @Description CorsConfig
 **/
@Configuration
public class CorsConfig implements WebMvcConfigurer {

    // 使用el表达式注入属性资源的值
    @Value("${itzixi.frontend.domain}")
    private String domain;

    @Override
    public void addCorsMappings(CorsRegistry registry) {

        registry.addMapping("/**")
                .allowedOrigins(domain.split(","))
                .allowedMethods("*")
                .allowedHeaders("*")
                .allowCredentials(true)
                .maxAge(60 * 60);

    }
}
