package com.itzixi.mapper;

import com.itzixi.pojo.bo.CandidateBO;
import com.itzixi.pojo.vo.CandidateVO;
import com.itzixi.pojo.vo.CandidateMatchVO;
import org.apache.ibatis.annotations.Param;

import java.util.List;
import java.util.Map;

public interface CandidateMapperCustom {

    public List<CandidateVO> queryCandidateList(@Param("paramMap") Map<String, Object> map);

    List<CandidateMatchVO> findAllByRealName(@Param("realName") String realName);

}
