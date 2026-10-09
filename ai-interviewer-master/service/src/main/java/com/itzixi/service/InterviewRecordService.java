package com.itzixi.service;

import com.itzixi.pojo.InterviewRecord;
import com.itzixi.pojo.vo.InterviewRecordVO;
import com.itzixi.utils.PagedGridResult;

import java.util.List;

public interface InterviewRecordService {

    /**
     * @Description: 保存面试结果
     * @Author 翙邑科技
     * @param interviewRecord
     */
    public void save(InterviewRecord interviewRecord);

    /**
     * @Description: 判断候选人是否面试过
     * @Author 翙邑科技
     * @param candidateId
     * @param jobName
     * @return boolean
     */
    public boolean checkExists(String candidateId, String jobName);

    public int findOffer_statusbyid(String candidateId);

    /**
     * @Description: 分页条件查询面试结果列表
     * @Author 翙邑科技
     * @param realName
//     * @param mobile
//     * @param jobId
     * @param page
     * @param pageSize
     * @return PagedGridResult
     */
    public PagedGridResult queryList(String realName,String mobile,Integer page, Integer pageSize);

    public PagedGridResult findById(String realName,String candidateId,String mobile, String jobId);

    public List<InterviewRecordVO> getResult(String candidateId);
}
