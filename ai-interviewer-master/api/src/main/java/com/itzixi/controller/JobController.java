package com.itzixi.controller;

import com.itzixi.grace.result.GraceJSONResult;
import com.itzixi.pojo.bo.JobBO;
import com.itzixi.service.JobService;
import jakarta.annotation.Resource;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;

/**
 * @ClassName JobController
 * @Author 公众号【翙邑科技】
 * @Version 1.0
 * @Description JobController
 **/
@RestController
@RequestMapping("job")
public class JobController {

    @Resource
    private JobService jobService;

    /**
     * @Description: 创建或者更新职位信息
     * @Author 翙邑科技
     * @param jobBO
     * @return GraceJSONResult
     */
    @PostMapping("createOrUpdate")
    public GraceJSONResult createOrUpdate(@RequestBody JobBO jobBO) {
        System.out.println(jobBO);
        jobService.createOrUpdate(jobBO);
        String companyInfo=jobBO.getCompanyInfo();
        String[] info=new String[100];
        info=companyInfo.split("\n");

        String jobid=jobBO.getId();
        for(int i=0;i<info.length;i++) {
            System.out.println("i:"+info[i]);
        }
        System.out.println(jobid);
        // 1. 构建目标接口URL
        String targetUrl = "http://10.10.10.100:8000/info";

        // 2. 封装请求头（multipart格式）
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_FORM_URLENCODED);

        // 3. 封装文件和其他参数
        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("id",jobid );
        body.add("info",companyInfo);;
        // 可添加其他参数：body.add("language", "zh-CN");
        // 4. 发送请求
        RestTemplate restTemplate = new RestTemplate();
        ResponseEntity<String> response = restTemplate.postForEntity(
                targetUrl,
                new HttpEntity<>(body, headers),
                String.class
        );
        System.out.println(response);
        return GraceJSONResult.ok();
    }

    /**
     * @Description: 分页查询职位信息列表
     * @Author 翙邑科技
     * @param page
     * @param pageSize
     * @return GraceJSONResult
     */
    @GetMapping("list")
    public GraceJSONResult list(@RequestParam(defaultValue = "1", name = "page") Integer page,
                                @RequestParam(defaultValue = "10", name = "pageSize") Integer pageSize) {

        System.out.println("123:"+jobService.queryList(page, pageSize));
        return GraceJSONResult.ok(jobService.queryList(page, pageSize));
    }

    /**
     * @Description: 查询职位详情
     * @Author 翙邑科技
     * @param jobId
     * @return GraceJSONResult
     */
    @GetMapping("detail")
    public GraceJSONResult detail(String jobId) {
        return GraceJSONResult.ok(jobService.getDetail(jobId));
    }

    /**
     * @Description: 删除职位详情
     * @Author 翙邑科技
     * @param jobId
     * @return GraceJSONResult
     */
    @PostMapping("delete")
    public GraceJSONResult delete(String jobId) {
        jobService.delete(jobId);
        return GraceJSONResult.ok();
    }

    /**
     * @Description: 查询并且获得所有包含名称的岗位列表
     * @Author 翙邑科技
     * @param
     * @return GraceJSONResult
     */
    @GetMapping("nameList")
    public GraceJSONResult nameList() {
        return GraceJSONResult.ok(jobService.nameList());
    }

}
