package com.itzixi.service;

import com.itzixi.pojo.Interviewer;
import com.itzixi.pojo.bo.InterviewerBO;

import java.util.List;

/**
 * @ClassName InterviewerService
 * @Author 公众号【翙邑科技】
 * @Version 1.0
 * @Description InterviewerService
 **/
public interface InterviewerService {

    /**
     * @Description: 新增或者修改面试官信息
     * @Author 翙邑科技
     * @param interviewerBO
     */
    public void createOrUpdate(InterviewerBO interviewerBO);

    /**
     * @Description: 查询所有的面试官数据列表
     * @Author 翙邑科技
     * @param
     * @return List<Interviewer>
     */
    public List<Interviewer> queryAll();

    /**
     * @Description: 删除数字人面试官
     * @Author 翙邑科技
     * @param interviewerId
     */
    public void delete(String interviewerId);
}
