package com.itzixi.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.itzixi.exception.GraceException;
import com.itzixi.grace.result.ResponseStatusEnum;
import com.itzixi.mapper.InterviewerMapper;
import com.itzixi.pojo.Interviewer;
import com.itzixi.pojo.bo.InterviewerBO;
import com.itzixi.service.InterviewerService;
import com.itzixi.service.JobService;
import com.itzixi.service.QuestionLibService;
import jakarta.annotation.Resource;
import org.apache.commons.lang3.StringUtils;
import org.springframework.beans.BeanUtils;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;

/**
 * @ClassName InterviewerServiceImpl
 * @Author 公众号【翙邑科技】
 * @Version 1.0
 * @Description InterviewerServiceImpl
 **/
@Service
public class InterviewerServiceImpl implements InterviewerService {

    @Resource
    private InterviewerMapper interviewerMapper;

    @Resource
    private JobService jobService;

    @Resource
    private QuestionLibService questionLibService;

    @Override
    public void createOrUpdate(InterviewerBO interviewerBO) {

        Interviewer interviewer = new Interviewer();
        BeanUtils.copyProperties(interviewerBO, interviewer);
        interviewer.setUpdatedTime(LocalDateTime.now());

        if (StringUtils.isBlank(interviewer.getId())) {
            interviewer.setCreateTime(LocalDateTime.now());
            interviewerMapper.insert(interviewer);
        } else {
            interviewerMapper.updateById(interviewer);
        }

    }

    @Override
    public List<Interviewer> queryAll() {
        return interviewerMapper.selectList(
                new QueryWrapper<Interviewer>()
                        .orderByDesc("updated_time")
        );
    }

    @Override
    public void delete(String interviewerId) {

        // 删除面试官之前需要判断有没有职位和面试题库正在使用（多表关联需要删除关联的数据）
        boolean jobFlag = jobService.isJobContainInterviewer(interviewerId);
        boolean questionFlag = questionLibService.isQuestionLibContainInterviewer(interviewerId);

        if (jobFlag || questionFlag) {
            GraceException.display(ResponseStatusEnum.CAN_NOT_DELETE_INTERVIEWER);
        }

        interviewerMapper.deleteById(interviewerId);
    }



}
