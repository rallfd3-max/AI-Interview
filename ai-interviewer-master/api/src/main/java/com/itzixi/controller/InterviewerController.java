package com.itzixi.controller;

import com.itzixi.grace.result.GraceJSONResult;
import com.itzixi.pojo.Interviewer;
import com.itzixi.pojo.bo.InterviewerBO;
import com.itzixi.service.InterviewerService;
import jakarta.annotation.Resource;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;

/**
 * @ClassName InterviewerController
 * @Author 公众号【翙邑科技】
 * @Version 1.0
 * @Description InterviewerController
 **/
@RestController
@RequestMapping("interviewer")
public class InterviewerController {

    @Resource
    private InterviewerService interviewerService;

    /**
     * @Description: 创建或者更新数字人面试官的信息
     * @Author 翙邑科技
     * @param interviewerBO
     * @return GraceJSONResult
     */
    @PostMapping("createOrUpdate")
    public GraceJSONResult createOrUpdate(@Valid @RequestBody InterviewerBO interviewerBO) {
        interviewerService.createOrUpdate(interviewerBO);
        return GraceJSONResult.ok();
    }

    /**
     * @Description: 查询所有数字人面试官列表
     * @Author 翙邑科技
     * @param
     * @return GraceJSONResult
     */
    @GetMapping("list")
    public GraceJSONResult list() {
        return GraceJSONResult.ok(interviewerService.queryAll());
    }

    /**
     * @Description: 删除数字人面试官
     * @Author 翙邑科技
     * @param interviewerId
     * @return GraceJSONResult
     */
    @DeleteMapping("delete")
    public GraceJSONResult delete(@RequestParam String interviewerId) {
        interviewerService.delete(interviewerId);
        return GraceJSONResult.ok();
    }
}
