package com.itzixi.service.impl;

import com.itzixi.mapper.AnswerRecordMapper;
import com.itzixi.pojo.Answer;
import com.itzixi.service.AnswerRecordService;
import jakarta.annotation.Resource;
import org.springframework.stereotype.Service;

/**
 * @ClassName AnswerServiceImpl
 * @Author 公众号【翙邑科技】
 * @Version 1.0
 * @Description AnswerServiceImpl
 **/
@Service
public class AnswerRecordServiceImpl implements AnswerRecordService {
    @Resource
    private AnswerRecordMapper answerRecordMapper;
    @Override
    public void save(Answer answer) {
        answerRecordMapper.insert(answer);
    }
}