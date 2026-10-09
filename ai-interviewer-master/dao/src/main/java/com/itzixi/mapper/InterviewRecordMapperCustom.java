package com.itzixi.mapper;

import com.itzixi.pojo.vo.InterviewRecordVO;
import org.apache.ibatis.annotations.Param;

import java.util.List;
import java.util.Map;

public interface InterviewRecordMapperCustom {

    public List<InterviewRecordVO> queryList(@Param("paramMap") Map<String, Object> map);

}
