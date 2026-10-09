package com.itzixi.utils;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.PropertySource;
import org.springframework.stereotype.Component;

/**
 * @ClassName TencentCloudProperties
 * @Author 公众号【翙邑科技】
 * @Version 1.0
 * @Description TencentCloudProperties
 **/
@Component
@Data
@PropertySource("classpath:tencentCloud.properties")
@ConfigurationProperties(prefix = "tencent.cloud")
public class TencentCloudProperties {

    private String secretId;
    private String secretKey;

}
