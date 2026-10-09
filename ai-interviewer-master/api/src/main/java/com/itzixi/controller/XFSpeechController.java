package com.itzixi.controller;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.itzixi.grace.result.GraceJSONResult;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.*;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("speech")
public class XFSpeechController {
    @PostMapping("/uploadVoice")
    public GraceJSONResult uploadFile(@RequestParam("file") MultipartFile file) throws Exception {
        // 1. 构建目标接口URL
        String targetUrl = "http://10.10.10.1:8001/recognize";

        // 2. 封装请求头（multipart格式）
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);

        // 3. 封装文件和其他参数
        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("audio", new ByteArrayResource(file.getBytes()) {
            @Override
            public String getFilename() {
                return file.getOriginalFilename(); // 保持原始文件名
            }
        });
        // 可添加其他参数：body.add("language", "zh-CN");

        // 4. 发送请求
        RestTemplate restTemplate = new RestTemplate();
        ResponseEntity<String> response = restTemplate.postForEntity(
                targetUrl,
                new HttpEntity<>(body, headers),
                String.class
        );
        System.out.println(response);
        String res = response.getBody();
        System.out.println(res);
        JsonObject jsonObject = JsonParser.parseString(res).getAsJsonObject();
        String textValue = jsonObject.get("text").getAsString();
        System.out.println("提取结果: " + textValue);
        // 5. 处理响应
        if (response.getStatusCode() == HttpStatus.OK) {
            return GraceJSONResult.ok(textValue);
        } else {
            return GraceJSONResult.errorMsg("识别服务调用失败");
        }
    }

}