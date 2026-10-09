package com.itzixi.service.impl;

import com.itzixi.pojo.Candidate;
import com.itzixi.pojo.Job;
import com.itzixi.pojo.vo.GlassesCandidateContextVO;
import com.itzixi.pojo.vo.InterviewRecordVO;
import com.itzixi.service.CandidateService;
import com.itzixi.service.GlassesCandidateContextService;
import com.itzixi.service.InterviewRecordService;
import com.itzixi.service.JobService;
import org.apache.commons.lang3.StringUtils;
import org.springframework.stereotype.Service;

import java.util.Collections;
import java.util.List;
import java.util.Optional;

/**
 * Aggregates existing business services without exposing Candidate entities to a device.
 */
@Service
public class GlassesCandidateContextServiceImpl implements GlassesCandidateContextService {

    private static final int DESCRIPTION_LIMIT = 240;

    private final CandidateService candidateService;
    private final JobService jobService;
    private final InterviewRecordService interviewRecordService;

    public GlassesCandidateContextServiceImpl(CandidateService candidateService,
                                               JobService jobService,
                                               InterviewRecordService interviewRecordService) {
        this.candidateService = candidateService;
        this.jobService = jobService;
        this.interviewRecordService = interviewRecordService;
    }

    @Override
    public Optional<GlassesCandidateContextVO> getContext(String candidateId) {
        if (StringUtils.isBlank(candidateId) || candidateId.length() > 64) {
            return Optional.empty();
        }

        Candidate candidate = candidateService.getDetail(candidateId);
        if (candidate == null) {
            return Optional.empty();
        }

        Job job = StringUtils.isBlank(candidate.getJobId()) ? null : jobService.getDetail(candidate.getJobId());
        List<InterviewRecordVO> records = interviewRecordService.getResult(candidateId);
        if (records == null) {
            records = Collections.emptyList();
        }
        InterviewRecordVO latestRecord = records.isEmpty() ? null : records.get(0);

        GlassesCandidateContextVO context = new GlassesCandidateContextVO();
        context.setCandidateId(candidate.getId());
        context.setRealName(candidate.getRealName());
        context.setGender(toGender(candidate.getSex()));
        context.setSchool(candidate.getSchool());
        context.setMajor(candidate.getMajor());
        context.setJobId(candidate.getJobId());
        context.setJobName(job == null ? candidate.getJob() : job.getJobName());
        context.setJobDescriptionSummary(job == null ? null : abbreviate(job.getJobDesc()));
        context.setCandidateProfile(abbreviate(candidate.getIntroduce()));
        context.setExperienceSummary(abbreviate(candidate.getExperiment()));
        context.setInterviewStatus(latestRecord == null ? "NOT_STARTED" : "COMPLETED");
        if (latestRecord != null) {
            context.setLatestInterviewSummary(abbreviate(firstNonBlank(
                    latestRecord.getInterviewresult(), latestRecord.getResult(), latestRecord.getAnswerContent())));
            context.setLatestInterviewScore(latestRecord.getTotalscore());
        }
        return Optional.of(context);
    }

    private String toGender(Integer sex) {
        if (sex == null) {
            return "UNKNOWN";
        }
        if (sex == 1) {
            return "男";
        }
        if (sex == 0) {
            return "女";
        }
        return "保密";
    }

    private String abbreviate(String value) {
        if (StringUtils.isBlank(value)) {
            return null;
        }
        String normalized = StringUtils.normalizeSpace(value);
        return StringUtils.abbreviate(normalized, DESCRIPTION_LIMIT);
    }

    private String firstNonBlank(String... values) {
        for (String value : values) {
            if (StringUtils.isNotBlank(value)) {
                return value;
            }
        }
        return null;
    }
}
