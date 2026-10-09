package com.itzixi.controller;

import com.itzixi.base.BaseInfoProperties;
import com.itzixi.grace.result.GraceJSONResult;
import com.itzixi.grace.result.ResponseStatusEnum;
import com.itzixi.pojo.Candidate;
import com.itzixi.pojo.bo.VerifySMSBO;
import com.itzixi.pojo.vo.CandidateVO;
import com.itzixi.service.CandidateService;
import com.itzixi.service.InterviewRecordService;
import com.itzixi.utils.JsonUtils;
import com.itzixi.utils.SMSUtils;
import jakarta.annotation.Resource;
import org.apache.commons.lang3.StringUtils;
import org.springframework.beans.BeanUtils;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

/**
 * @ClassName WelcomeController
 * @Author 公众号【翙邑科技】
 * @Version 1.0
 * @Description WelcomeController
 **/
@RestController
@RequestMapping("welcome")
public class WelcomeController extends BaseInfoProperties {

    @Resource
    private SMSUtils smsUtils;

    @Resource
    private CandidateService candidateService;

    @Resource
    private InterviewRecordService interviewRecordService;

    /**
     * @Description: 获得短信验证码
     * @Author 翙邑科技
     * @param mobile
     * @return GraceJSONResult
     */
    @GetMapping("getSMSCode")
    public GraceJSONResult getSMSCode(String mobile) throws Exception {
        System.out.println(mobile);
        if (StringUtils.isBlank(mobile)) return GraceJSONResult.error();

        String code = (int)((Math.random() * 9 + 1) * 100000) + "";
//        sms.send(mobile,code);
        System.out.println(code);
//        smsUtils.sendSMS(mobile, code);

        // 把验证码存入到redis中，用于后续进入面试的校验
        redis.set(MOBILE_SMSCODE + ":" + mobile, code, 10 * 60);

        return GraceJSONResult.ok();
    }

    /**
     * @Description: 校验用户能否进入面试流程
     * @Author 翙邑科技
     * @param verifySMSBO
     * @return GraceJSONResult
     */
    @PostMapping("verify")
    public GraceJSONResult verify(@Validated @RequestBody VerifySMSBO verifySMSBO) {

        String mobile = verifySMSBO.getMobile();
        String code = verifySMSBO.getSmsCode();

        // 1. 从Redis获得验证码进行校验判断是否匹配
        String redisCode  = redis.get(MOBILE_SMSCODE + ":" + mobile);
        if (StringUtils.isBlank(redisCode) || !redisCode.equalsIgnoreCase(code)) {
           return GraceJSONResult.errorCustom(ResponseStatusEnum.SMS_CODE_ERROR);
        }

        // 2. 根据mobile查询数据库，判断用户是否存在，是否是候选人
        Candidate candidate = candidateService.queryMobileIsExist(mobile);
        if (candidate == null) {
            // 2.1 如果查询的用户为空，则表示该用户不是候选人，无法进入面试流程
            return GraceJSONResult.errorCustom(ResponseStatusEnum.USER_INFO_NOT_EXIST_ERROR);
        }
//        else {
//            // 2.2 如果不为空，则需要判断用户是否已经面试过，如果面试过，则无法再次面试
//            boolean isExist = interviewRecordService.isCandidateRecordExist(candidate.getId());
//            if (isExist)
//                return GraceJSONResult.errorCustom(ResponseStatusEnum.USER_ALREADY_DID_INTERVIEW_ERROR);
//        }

        // 3. 保存用户token信息，保存分布式会话到Redis中
        String uToken = UUID.randomUUID().toString();
        redis.set(REDIS_USER_TOKEN + ":" + candidate.getId(), uToken, 3 * 60 * 60);

        CandidateVO candidateVO = new CandidateVO();
        BeanUtils.copyProperties(candidate, candidateVO);
        candidateVO.setUserToken(uToken);
        candidateVO.setCandidateId(candidate.getId());

        // 4. 用户进入面试流程后（登录以后），删除Redis中的验证码
        redis.del(MOBILE_SMSCODE + ":" + mobile);

        // 5. (可选)用户信息保存到服务端Redis中，保存8小时或者4小时
        redis.set(REDIS_USER_INFO + ":" + candidate.getId(), JsonUtils.objectToJson(candidateVO), 3 * 60 * 60);

        // 6. 返回用户信息给前端
        return GraceJSONResult.ok(candidateVO);
    }

}
