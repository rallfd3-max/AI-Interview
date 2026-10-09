package com.itzixi.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.github.pagehelper.PageHelper;
import com.itzixi.base.BaseInfoProperties;
import com.itzixi.enums.YesOrNo;
import com.itzixi.mapper.QuestionLibMapper;
import com.itzixi.mapper.QuestionLibMapperCustom;
import com.itzixi.pojo.QuestionLib;
import com.itzixi.pojo.bo.QuestionLibBO;
import com.itzixi.pojo.vo.InitQuestionsVO;
import com.itzixi.pojo.vo.QuestionLibVO;
import com.itzixi.service.CandidateService;
import com.itzixi.service.JobService;
import com.itzixi.service.QuestionLibService;
import com.itzixi.utils.PagedGridResult;
import jakarta.annotation.Resource;
import org.apache.commons.lang3.StringUtils;
import org.springframework.beans.BeanUtils;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.*;

/**
 * @ClassName QuestionLibServiceImpl
 * @Author 公众号【翙邑科技】
 * @Version 1.0
 * @Description QuestionLibServiceImpl
 **/
@Service
public class QuestionLibServiceImpl extends BaseInfoProperties implements QuestionLibService {

    @Resource
    private QuestionLibMapper questionLibMapper;

    @Resource
    private QuestionLibMapperCustom questionLibMapperCustom;

    @Resource
    private CandidateService candidateService;

    @Resource
    private JobService jobService;

    @Override
    public void createOrUpdate(QuestionLibBO questionLibBO) {

        QuestionLib questionLib = new QuestionLib();
        BeanUtils.copyProperties(questionLibBO, questionLib);
        questionLib.setUpdatedTime(LocalDateTime.now());

        if (StringUtils.isBlank(questionLib.getId())) {
            questionLib.setIsOn(YesOrNo.YES.type);
            questionLib.setCreateTime(LocalDateTime.now());
            questionLibMapper.insert(questionLib);
        } else {
            questionLibMapper.updateById(questionLib);
        }

    }

    @Override
    public PagedGridResult queryList(String aiName, String question, Integer page, Integer pageSize) {

        PageHelper.startPage(page, pageSize);

        Map<String, Object> map = new HashMap<>();
        if (StringUtils.isNotBlank(aiName)) {
            map.put("aiName", aiName);
        }
        if (StringUtils.isNotBlank(question)) {
            map.put("question", question);
        }

        List<QuestionLibVO> list =  questionLibMapperCustom.queryQuestionLibList(map);

        return setterPagedGrid(list, page);
    }

    @Override
    public void setDisplayOrNot(String questionLibId, Integer isOn) {

        QuestionLib questionLib = new QuestionLib();
        questionLib.setId(questionLibId);
        questionLib.setIsOn(isOn);
        questionLib.setUpdatedTime(LocalDateTime.now());

        questionLibMapper.updateById(questionLib);
    }

    @Override
    public void delete(String questionLibId) {
        questionLibMapper.deleteById(questionLibId);
    }

    @Override
    public boolean isQuestionLibContainInterviewer(String InterviewerId) {
        QueryWrapper<QuestionLib> queryWrapper = new QueryWrapper<>();
        queryWrapper.eq("interviewer_id", InterviewerId);

        Long counts = questionLibMapper.selectCount(queryWrapper);

        return counts > 0 ? true : false;
    }

    @Override
    public List<InitQuestionsVO> getRandomQuestions(String jobName, Integer questionNum) {


        String interviewerId = jobService.getDetailByName(jobName).getInterviewerId();

        // 2. 根据面试官获得其所有面试题总数
        Long questionCounts = questionLibMapper.selectCount(
            new QueryWrapper<QuestionLib>()
                    .eq("interviewer_id", interviewerId)
        );

        // 3. 根据题库总数获得指定数量的面试题
        List<Long> randomList = new ArrayList<>();
        for (int i = 0 ; i < questionNum ; i ++) {
            Random random = new Random();
            long randomNum = random.nextLong(questionCounts);

            if (randomList.contains(randomNum)) {
                // 如果包含则继续循环，累加questionNum平衡循环次数
                questionNum ++;
                System.out.println(questionNum);
                continue;
            } else {
                randomList.add(randomNum);
            }
        }

        // 4. 根据索引下标从数据库中获得面试题
        List<InitQuestionsVO> questionList = new ArrayList<>();
        for (Long l : randomList) {
            Map<String, Object> map = new HashMap<>();
            map.put("indexNum", l);

            InitQuestionsVO question = questionLibMapperCustom.queryRandomQuestion(map);
            questionList.add(question);
        }

        return questionList;
    }
}
