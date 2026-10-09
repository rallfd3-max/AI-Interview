package com.itzixi.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.github.pagehelper.PageHelper;
import com.itzixi.base.BaseInfoProperties;
import com.itzixi.mapper.InterviewRecordMapper;
import com.itzixi.mapper.InterviewRecordMapperCustom;
import com.itzixi.pojo.InterviewRecord;
import com.itzixi.pojo.vo.InterviewRecordVO;
import com.itzixi.service.InterviewRecordService;
import com.itzixi.utils.PagedGridResult;
import jakarta.annotation.Resource;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * @ClassName InterviewRecordServiceImpl
 * @Author 公众号【翙邑科技】
 * @Version 1.0
 * @Description InterviewRecordServiceImpl
 **/
@Service
public class InterviewRecordServiceImpl extends BaseInfoProperties implements InterviewRecordService {

    @Resource
    private InterviewRecordMapper interviewRecordMapper;

    @Resource
    private InterviewRecordMapperCustom interviewRecordMapperCustom;

    @Override
    public void save(InterviewRecord interviewRecord) {
        interviewRecordMapper.insert(interviewRecord);
    }

    @Override
    public boolean checkExists(String candidateId, String jobName) {
        return interviewRecordMapper.selectCount(
                new QueryWrapper<InterviewRecord>()
                        .eq("candidate_id", candidateId)
                        .eq("job_name", jobName)
        ) > 0;
    }
    @Override
    public int findOffer_statusbyid(String candidateId) {
        List<InterviewRecord> list = interviewRecordMapper.selectList(
                new QueryWrapper<InterviewRecord>()
                        .eq("candidate_id",candidateId)
        );
        return list.get(0).isOffer_status();
    }

    @Override
    public PagedGridResult queryList(String realName,String mobile,Integer page, Integer pageSize) {

        PageHelper.startPage(page, pageSize);

        Map<String, Object> map = new HashMap<>();
        map.put("realName", realName);
        map.put("mobile", mobile);
//        map.put("jobId",jobId);
//        map.put("candidateId",candidateId);

        List<InterviewRecordVO> list = interviewRecordMapperCustom.queryList(map);
        return setterPagedGrid(list, page);
    }

    @Override
    public PagedGridResult findById(String realName, String candidateId, String mobile, String jobId) {
        Map<String, Object> map = new HashMap<>();
        map.put("realName", realName);
        map.put("candidateId",candidateId);
        map.put("mobile", mobile);
        map.put("jobId",jobId);
        List<InterviewRecordVO> list = interviewRecordMapperCustom.queryList(map);
        return setterPagedGrid(list, 1);
    }

    @Override
    public List<InterviewRecordVO> getResult(String candidateId) {
        Map<String, Object> map = new HashMap<>();
        map.put("candidateId",candidateId);
        List<InterviewRecordVO> list = interviewRecordMapperCustom.queryList(map);
        return list;
    }

}
