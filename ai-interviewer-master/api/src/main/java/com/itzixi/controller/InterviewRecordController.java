package com.itzixi.controller;

import com.itzixi.ChatGLMTask;
import com.itzixi.grace.result.GraceJSONResult;
import com.itzixi.pojo.bo.SubmitAnswerBO;
import com.itzixi.service.InterviewRecordService;
import com.itzixi.utils.PagedGridResult;
import jakarta.annotation.Resource;
import org.springframework.web.bind.annotation.*;

/**
 * @ClassName InterviewRecordController
 * @Author 公众号【翙邑科技】
 * @Version 1.0
 * @Description InterviewRecordController
 **/
@RestController
@RequestMapping("interviewRecord")
public class InterviewRecordController {

    @Resource
    private ChatGLMTask chatGLMTask;

    @Resource
    private InterviewRecordService interviewRecordService;

    /**
     * @Description: 提交面试的回答内容进行AI分析
     * @Author 翙邑科技
     * @param submitAnswerBO
     * @return GraceJSONResult
     */
    @PostMapping("collect")
    public GraceJSONResult collect(@RequestBody SubmitAnswerBO submitAnswerBO) {
        chatGLMTask.display(submitAnswerBO);
        return GraceJSONResult.ok();
    }

    /**
     * @Description: 分页查询条件搜索面试记录列表
     * @Author 翙邑科技
     * @param realName
     * @param mobile
//     * @param jobId
//     * @param candidateId
     * @param page
     * @param pageSize
     * @return GraceJSONResult
     */
    @GetMapping("list")
    public GraceJSONResult list(@RequestParam String realName,
                                @RequestParam String mobile,
//                                @RequestParam String jobId,
//                                @RequestParam String candidateId,
                                @RequestParam(defaultValue = "1", name = "page") Integer page,
                                @RequestParam(defaultValue = "10", name = "pageSize") Integer pageSize) {

        PagedGridResult result = interviewRecordService.queryList(realName, mobile,page, pageSize);
        System.out.println(result);
        return GraceJSONResult.ok(result);
    }
    @GetMapping("findById")
    public GraceJSONResult findById(@RequestParam String realName,
                                    @RequestParam String candidateId,
                                    @RequestParam String mobile,
                                @RequestParam String jobId) {
        PagedGridResult result = interviewRecordService.findById(realName, candidateId,mobile,jobId);
        System.out.println(result);
        return GraceJSONResult.ok(result);
    }
    /**
     * @Description: 检查是否有面试记录
     * @Author 翙邑科技
     * @param candidateId
     * @param jobName
     * @return GraceJSONResult
     */
    @GetMapping("/check")
    public GraceJSONResult checkInterviewRecord(
            @RequestParam String candidateId,
            @RequestParam String jobName) {

        boolean exists = interviewRecordService.checkExists(candidateId, jobName);
        return GraceJSONResult.ok(exists);
    }
    @GetMapping("/get")
    public GraceJSONResult getInterviewResult(
            @RequestParam String candidateId
    ){
        return GraceJSONResult.ok(interviewRecordService.getResult(candidateId));
    }

}
