package com.itzixi.pojo;

import com.baomidou.mybatisplus.annotation.TableName;

import java.io.Serializable;

/**
 * <p>
 * 面试记录表
 * </p>
 *
 * @author 翙邑科技
 * @since 2024-10-04
 */
@TableName("answer_record")
public class Answer implements Serializable {

    private static final long serialVersionUID = 1L;

    private String id;

    /**
     * 应聘者id
     */
    private String candidateId;

    /**
     * 职位名称，快照名称，原字段可能会更改
     */
    private String jobName;

    /**
     * 应聘者的回答内容
     */
    private String answer;


    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getCandidateId() {
        return candidateId;
    }

    public void setCandidateId(String candidateId) {
        this.candidateId = candidateId;
    }

    public String getJobName() {
        return jobName;
    }

    public void setJobName(String jobName) {
        this.jobName = jobName;
    }

    public String getAnswer() {
        return answer;
    }

    public void setAnswer(String answer) {
        this.answer = answer;
    }

    @Override
    public String toString() {
        return "InterviewRecord{" +
                "id = " + id +
                ", candidateId = " + candidateId +
                ", jobName = " + jobName +
                ",answer="+answer+
                "}";
    }
}
