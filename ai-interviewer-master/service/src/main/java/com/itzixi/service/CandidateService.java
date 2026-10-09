package com.itzixi.service;

import com.itzixi.pojo.Candidate;
import com.itzixi.pojo.bo.CandidateBO;
import com.itzixi.utils.PagedGridResult;
import com.itzixi.pojo.vo.CandidateMatchResultVO;

public interface CandidateService {

    /**
     * @Description: 创建或者更新候选人（应聘者）的信息
     * @Author 翙邑科技
     * @param candidateBO
     */
    public void createOrUpdate(CandidateBO candidateBO);

    /**
     * @Description: 查询候选人（应聘者）列表
     * @Author 翙邑科技
     * @param realName
     * @param mobile
     * @param page
     * @param pageSize
     * @return PagedGridResult
     */
    public PagedGridResult queryList(String realName, String mobile, Integer page, Integer pageSize);

    /**
     * @Description: 获得候选人信息详情
     * @Author 翙邑科技
     * @param candidateId
     */
    public Candidate getDetail(String candidateId);

    /**
     * @Description: 删除候选人
     * @Author 翙邑科技
     * @param candidateId
     */
    public void delete(String candidateId);

    /**
     * @Description: 判断用户是否存在，如果存在返回用户信息，如果不存在返回null
     * @Author 翙邑科技
     * @param mobile
     * @return Candidate
     */
    public Candidate queryMobileIsExist(String mobile);

    CandidateMatchResultVO matchByRealName(String realName);
}
