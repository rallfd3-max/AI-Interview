package com.itzixi.mapper;

import com.itzixi.pojo.Job;
import com.itzixi.pojo.vo.JobVO;
import org.apache.ibatis.annotations.Param;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

public interface JobMapperCustom {

    public List<JobVO> queryJobList(@Param("paramMap") Map<String, Object> map);

    public List<HashMap<String, String>> queryNameList(@Param("paramMap") Map<String, Object> map);

    Job selectByjobName(String jobName);
}
