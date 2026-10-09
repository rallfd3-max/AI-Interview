package com.itzixi.controller;

import com.itzixi.grace.result.GraceJSONResult;
import com.itzixi.pojo.bo.CandidateBO;
import com.itzixi.service.CandidateService;
import com.itzixi.utils.PagedGridResult;
import jakarta.annotation.Resource;
import org.springframework.web.bind.annotation.*;
import org.apache.commons.lang3.StringUtils;

/**
 * @ClassName CandidateController
 * @Author 公众号【翙邑科技】
 * @Version 1.0
 * @Description CandidateController
 **/
@RestController
@RequestMapping("candidate")
public class CandidateController {

    @Resource
    private CandidateService candidateService;

    /**
     * @Description: 创建或者更新候选人的信息
     * @Author 翙邑科技
     * @param candidateBO
     * @return GraceJSONResult
     */
    @PostMapping("createOrUpdate")
    public GraceJSONResult createOrUpdate(@RequestBody CandidateBO candidateBO) {
        candidateService.createOrUpdate(candidateBO);
        return GraceJSONResult.ok();
    }

    /**
     * @Description: 条件搜索候选人的列表
     * @Author 翙邑科技
     * @param realName
     * @param mobile
     * @param page
     * @param pageSize
     * @return GraceJSONResult
     */
    @GetMapping("list")
    public GraceJSONResult list(@RequestParam(defaultValue = "") String realName,
                                @RequestParam(defaultValue = "") String mobile,
                                @RequestParam(defaultValue = "1", name = "page") Integer page,
                                @RequestParam(defaultValue = "10", name = "pageSize") Integer pageSize) {
        PagedGridResult result = candidateService.queryList(realName, mobile, page, pageSize);
        return GraceJSONResult.ok(result);
    }

    @GetMapping("match")
    public GraceJSONResult match(@RequestParam String name) {
        if (StringUtils.isBlank(name)) {
            return GraceJSONResult.errorMsg("姓名不能为空");
        }
        return GraceJSONResult.ok(candidateService.matchByRealName(name));
    }

    /**
     * @Description: 查询候选人
     * @Author 翙邑科技
     * @param candidateId
     * @return GraceJSONResult
     */
    @GetMapping("detail")
    public GraceJSONResult detail(@RequestParam String candidateId) {

        return GraceJSONResult.ok(candidateService.getDetail(candidateId));
    }

    /**
     * @Description: 删除候选人
     * @Author 翙邑科技
     * @param candidateId
     * @return GraceJSONResult
     */
    @PostMapping("delete")
    public GraceJSONResult delete(@RequestParam String candidateId) {
        candidateService.delete(candidateId);
        return GraceJSONResult.ok();
    }
}
