package com.itzixi.service;

import com.itzixi.pojo.bo.QuestionLibBO;
import com.itzixi.pojo.vo.InitQuestionsVO;
import com.itzixi.utils.PagedGridResult;

import java.util.List;

public interface QuestionLibService {

    /**
     * @Description: 创建或者更新题库
     * @Author 翙邑科技
     * @param questionLibBO
     */
    public void createOrUpdate(QuestionLibBO questionLibBO);

    /**
     * @Description: 分页查询题库列表
     * @Author 翙邑科技
     * @param aiName
     * @param question
     * @param page
     * @param pageSize
     * @return PagedGridResult
     */
    public PagedGridResult queryList(String aiName, String question, Integer page, Integer pageSize);

    /**
     * @Description: 启用或者禁用某个面试题
     * @Author 翙邑科技
     * @param questionLibId
     * @param isOn
     */
    public void setDisplayOrNot(String questionLibId, Integer isOn);

    /**
     * @Description: 删除面试题
     * @Author 翙邑科技
     * @param questionLibId
     */
    public void delete(String questionLibId);

    /**
     * @Description: 判断所有面试题库中是否包含某个面试官
     * @Author 翙邑科技
     * @param InterviewerId
     * @return boolean
     */
    public boolean isQuestionLibContainInterviewer(String InterviewerId);

    /**
     * @Description: 获得指定数量的随机面试题
     * @Author 翙邑科技
     * @param jobId
     * @param questionNum
     * @return List<InitQuestionsVO>
     */
    public List<InitQuestionsVO> getRandomQuestions(String jobId, Integer questionNum);
}
