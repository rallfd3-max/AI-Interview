package com.itzixi.mapper;

import com.itzixi.pojo.vo.InitQuestionsVO;
import com.itzixi.pojo.vo.QuestionLibVO;
import org.apache.ibatis.annotations.Param;

import java.util.List;
import java.util.Map;

/**
 * <p>
 * 面试题库表（每个数字人面试官都会对应一些面试题） Mapper 接口
 * </p>
 *
 * @author 翙邑科技
 * @since 2024-10-04
 */
public interface QuestionLibMapperCustom {

    public List<QuestionLibVO> queryQuestionLibList(@Param("paramMap") Map<String, Object> map);

    public InitQuestionsVO queryRandomQuestion(@Param("paramMap") Map<String, Object> map);

}
