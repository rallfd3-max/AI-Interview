package com.itzixi.controller;

import com.itzixi.base.BaseInfoProperties;
import com.itzixi.enums.YesOrNo;
import com.itzixi.grace.result.GraceJSONResult;
import com.itzixi.grace.result.ResponseStatusEnum;
import com.itzixi.pojo.bo.QuestionLibBO;
import com.itzixi.pojo.vo.InitQuestionsVO;
import com.itzixi.service.QuestionLibService;
import com.itzixi.utils.PagedGridResult;
import jakarta.annotation.Resource;
import org.apache.commons.lang3.StringUtils;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * @ClassName QuestionLibController
 * @Author 公众号【翙邑科技】
 * @Version 1.0
 * @Description QuestionLibController
 **/
@RestController
@RequestMapping("questionLib")
public class QuestionLibController extends BaseInfoProperties {

    @Resource
    private QuestionLibService questionLibService;

    @PostMapping("createOrUpdate")
    public GraceJSONResult createOrUpdate(@RequestBody QuestionLibBO questionLibBO) {
        questionLibService.createOrUpdate(questionLibBO);
        return GraceJSONResult.ok();
    }

    /**
     * @Description: 分页查询面试题库列表
     * @Author 翙邑科技
     * @param aiName
     * @param question
     * @param page
     * @param pageSize
     * @return GraceJSONResult
     */
    @GetMapping("list")
    public GraceJSONResult list(@RequestParam String aiName,
                                @RequestParam String question,
                                @RequestParam(defaultValue = "1", name = "page") Integer page,
                                @RequestParam(defaultValue = "10", name = "pageSize") Integer pageSize) {

        PagedGridResult result = questionLibService.queryList(aiName, question, page, pageSize);
        return GraceJSONResult.ok(result);
    }

    /**
     * @Description: 设置某个面试题显示（启用）
     * @Author 翙邑科技
     * @param questionLibId
     * @return GraceJSONResult
     */
    @PostMapping("show")
    public GraceJSONResult show(@RequestParam String questionLibId) {
        if (StringUtils.isBlank(questionLibId)) return GraceJSONResult.error();
        questionLibService.setDisplayOrNot(questionLibId, YesOrNo.YES.type);
        return GraceJSONResult.ok();
    }

    /**
     * @Description: 设置某个面试题隐藏（禁用）
     * @Author 翙邑科技
     * @param questionLibId
     * @return GraceJSONResult
     */
    @PostMapping("hide")
    public GraceJSONResult hide(@RequestParam String questionLibId) {
        if (StringUtils.isBlank(questionLibId)) return GraceJSONResult.error();
        questionLibService.setDisplayOrNot(questionLibId, YesOrNo.NO.type);
        return GraceJSONResult.ok();
    }

    /**
     * @Description: 删除指定的面试题
     * @Author 翙邑科技
     * @param questionLibId
     * @return GraceJSONResult
     */
    @PostMapping("delete")
    public GraceJSONResult delete(@RequestParam String questionLibId) {
        if (StringUtils.isBlank(questionLibId)) return GraceJSONResult.error();
        questionLibService.delete(questionLibId);
        return GraceJSONResult.ok();
    }

    /**
     * @Description: 准备面试题，随机获得一定数量的面试题返回给前端
     * @Author 翙邑科技
     * @param jobName
     * @param candidateId
     * @return GraceJSONResult
     */
    @GetMapping("prepareQuestion")
    public GraceJSONResult prepareQuestion(@RequestParam String candidateId,String jobName) {

        // 判断应聘者候选人是否在会话中，限制接口被恶意调用
        String candidateInfo = redis.get(REDIS_USER_INFO + ":" + candidateId);
        String userToken = redis.get(REDIS_USER_TOKEN + ":" + candidateId);
        if (StringUtils.isBlank(candidateInfo) || StringUtils.isBlank(userToken)) {
            return GraceJSONResult.errorCustom(ResponseStatusEnum.USER_INFO_NOT_EXIST_ERROR);
        }

        List<InitQuestionsVO> result = questionLibService.getRandomQuestions(jobName, 3);
        return GraceJSONResult.ok(result);
    }

}
