package com.itzixi.pojo;

import com.baomidou.mybatisplus.annotation.TableName;

import java.io.Serializable;
import java.time.LocalDateTime;

/**
 * <p>
 * 面试记录表
 * </p>
 *
 * @author 翙邑科技
 * @since 2024-10-04
 */
@TableName("interview_record")
public class InterviewRecord implements Serializable {

    private static final long serialVersionUID = 1L;

    private String id;

    /**
     * 应聘者id
     */
    private String candidateId;
    private String jobId;

    /**
     * 职位名称，快照名称，原字段可能会更改
     */
    private String jobName;

    /**
     * 应聘者的回答内容
     */
    private String answerContent;

    /**
     * 整个面试所花费的总时间，单位：秒
     */
    private Integer takeTime;

    /**
     * 面试结果详情
     */
    private String result;

    private LocalDateTime createTime;

    private LocalDateTime updatedTime;

    private int offer_status;
    private Integer totalscore;
    private  String analysis;
    private String interviewresult;
    public InterviewRecord() {
    }

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

    public String getJobId() {
        return jobId;
    }

    public void setJobId(String jobId) {
        this.jobId = jobId;
    }

    public String getJobName() {
        return jobName;
    }

    public void setJobName(String jobName) {
        this.jobName = jobName;
    }

    public String getAnswerContent() {
        return answerContent;
    }

    public void setAnswerContent(String answerContent) {
        this.answerContent = answerContent;
    }

    public Integer getTakeTime() {
        return takeTime;
    }

    public void setTakeTime(Integer takeTime) {
        this.takeTime = takeTime;
    }

    public String getResult() {
        return result;
    }

    public void setResult(String result) {
        this.result = result;
    }

    public LocalDateTime getCreateTime() {
        return createTime;
    }

    public void setCreateTime(LocalDateTime createTime) {
        this.createTime = createTime;
    }

    public LocalDateTime getUpdatedTime() {
        return updatedTime;
    }

    public void setUpdatedTime(LocalDateTime updatedTime) {
        this.updatedTime = updatedTime;
    }

    public Integer getTotalscore() {
        return totalscore;
    }

    public int isOffer_status() {
        return offer_status;
    }

    public void setOffer_status(int offer_status) {
        this.offer_status = offer_status;
    }

    public void setTotalscore(Integer totalscore) {
        this.totalscore = totalscore;
    }

    public String getAnalysis() {
        return analysis;
    }

    public void setAnalysis(String analysis) {
        this.analysis = analysis;
    }

    public String getInterviewresult() {
        return interviewresult;
    }

    public void setInterviewresult(String interviewresult) {
        this.interviewresult = interviewresult;
    }

    @Override
    public String toString() {
        return "InterviewRecord{" +
        "id = " + id +
        ", candidateId = " + candidateId +
        ", jobName = " + jobName +
        ", answerContent = " + answerContent +
        ", takeTime = " + takeTime +
        ", result = " + result +
        ", createTime = " + createTime +
        ", updatedTime = " + updatedTime +
        ", totalscore = " + totalscore+
        ",offer_status ="+offer_status+
        ",analysis="+analysis+
        ",interviewresult="+interviewresult+
        "}";
    }
}
