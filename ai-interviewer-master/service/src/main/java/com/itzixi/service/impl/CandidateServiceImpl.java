package com.itzixi.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.github.pagehelper.PageHelper;
import com.itzixi.base.BaseInfoProperties;
import com.itzixi.mapper.CandidateMapper;
import com.itzixi.mapper.CandidateMapperCustom;
import com.itzixi.pojo.Candidate;
import com.itzixi.pojo.bo.CandidateBO;
import com.itzixi.pojo.vo.CandidateVO;
import com.itzixi.pojo.vo.CandidateMatchVO;
import com.itzixi.pojo.vo.CandidateMatchResultVO;
import com.itzixi.service.CandidateService;
import com.itzixi.utils.PagedGridResult;
import jakarta.annotation.Resource;
import org.apache.commons.lang3.StringUtils;
import org.springframework.beans.BeanUtils;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * @ClassName CandidateServiceImpl
 * @Author 公众号【翙邑科技】
 * @Version 1.0
 * @Description CandidateServiceImpl
 **/
@Service
public class CandidateServiceImpl extends BaseInfoProperties implements CandidateService {

    @Resource
    private CandidateMapper candidateMapper;

    @Resource
    private CandidateMapperCustom candidateMapperCustom;

    @Override
    public void createOrUpdate(CandidateBO candidateBO) {

        Candidate candidate = new Candidate();
        BeanUtils.copyProperties(candidateBO, candidate);
        candidate.setUpdatedTime(LocalDateTime.now());

        candidate.setJobId(candidateBO.getJobId());
        System.out.println(candidateBO.getJobId());
        if (StringUtils.isBlank(candidate.getId())) {
            candidate.setCreatedTime(LocalDateTime.now());
            candidateMapper.insert(candidate);
        } else {
            candidateMapper.updateById(candidate);
        }

    }

    @Override
    public PagedGridResult queryList(String realName, String mobile, Integer page, Integer pageSize) {

        PageHelper.startPage(page, pageSize);

        Map<String, Object> map = new HashMap<>();
        map.put("realName", realName);
        map.put("mobile", mobile);

        List<CandidateVO> list = candidateMapperCustom.queryCandidateList(map);

        return setterPagedGrid(list, page);
    }

    @Override
    public Candidate getDetail(String candidateId) {
        return candidateMapper.selectById(candidateId);
    }

    @Override
    public void delete(String candidateId) {
        candidateMapper.deleteById(candidateId);
    }

    @Override
    public Candidate queryMobileIsExist(String mobile) {
        return candidateMapper.selectOne(
                    new QueryWrapper<Candidate>()
                        .eq("mobile", mobile)
        );
    }

    @Override
    public CandidateMatchResultVO matchByRealName(String realName) {
        String normalizedName = StringUtils.trim(realName);
        List<CandidateMatchVO> candidates = candidateMapperCustom.findAllByRealName(normalizedName);
        return new CandidateMatchResultVO(normalizedName, candidates.size(), candidates);
    }
}
