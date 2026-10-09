package com.itzixi.test;

import com.itzixi.pojo.Candidate;
import com.itzixi.pojo.Job;
import com.itzixi.pojo.vo.GlassesCandidateContextVO;
import com.itzixi.pojo.vo.InterviewRecordVO;
import com.itzixi.service.CandidateService;
import com.itzixi.service.InterviewRecordService;
import com.itzixi.service.JobService;
import com.itzixi.service.impl.GlassesCandidateContextServiceImpl;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class GlassesCandidateContextServiceTest {

    private final CandidateService candidateService = mock(CandidateService.class);
    private final JobService jobService = mock(JobService.class);
    private final InterviewRecordService interviewRecordService = mock(InterviewRecordService.class);
    private final GlassesCandidateContextServiceImpl service = new GlassesCandidateContextServiceImpl(
            candidateService, jobService, interviewRecordService);

    @Test
    void loadsOnlyTheHumanSelectedCandidateIdAndFiltersPii() {
        Candidate selected = new Candidate();
        selected.setId("202");
        selected.setRealName("张三");
        selected.setSex(0);
        selected.setSchool("第二大学");
        selected.setMajor("软件工程");
        selected.setJobId("job-2");
        selected.setMobile("13900001234");
        selected.setIdentityNum("110101199001011234");
        selected.setAddress("不应发送的地址");
        selected.setEmail("zhangsan@example.com");
        selected.setIntroduce("候选人简介");
        selected.setExperiment("项目经历");
        when(candidateService.getDetail("202")).thenReturn(selected);

        Job job = new Job();
        job.setId("job-2");
        job.setJobName("测试工程师");
        job.setJobDesc("负责质量保障和自动化测试。");
        when(jobService.getDetail("job-2")).thenReturn(job);

        InterviewRecordVO record = new InterviewRecordVO();
        record.setCandidateId("202");
        record.setInterviewresult("复试通过，沟通清晰。");
        record.setTotalscore("90");
        when(interviewRecordService.getResult("202")).thenReturn(List.of(record));

        GlassesCandidateContextVO result = service.getContext("202").orElseThrow();

        assertEquals("202", result.getCandidateId());
        assertEquals("张三", result.getRealName());
        assertEquals("女", result.getGender());
        assertEquals("测试工程师", result.getJobName());
        assertEquals("COMPLETED", result.getInterviewStatus());
        assertEquals("90", result.getLatestInterviewScore());
        assertEquals("复试通过，沟通清晰。", result.getLatestInterviewSummary());
        assertFalse(hasProperty(GlassesCandidateContextVO.class, "mobile"));
        assertFalse(hasProperty(GlassesCandidateContextVO.class, "identityNum"));
        assertFalse(hasProperty(GlassesCandidateContextVO.class, "address"));
        assertFalse(hasProperty(GlassesCandidateContextVO.class, "email"));
        verify(candidateService).getDetail("202");
        verify(candidateService, never()).getDetail("101");
    }

    @Test
    void returnsEmptyForUnknownOrInvalidCandidateId() {
        when(candidateService.getDetail("404")).thenReturn(null);

        assertTrue(service.getContext("404").isEmpty());
        assertTrue(service.getContext(" ").isEmpty());
        assertTrue(service.getContext("x".repeat(65)).isEmpty());
        verify(candidateService).getDetail("404");
        verify(candidateService, never()).getDetail(" ");
    }

    @Test
    void handlesCandidateWithoutJobOrInterview() {
        Candidate candidate = new Candidate();
        candidate.setId("303");
        candidate.setRealName("李四");
        candidate.setSex(2);
        when(candidateService.getDetail("303")).thenReturn(candidate);
        when(interviewRecordService.getResult("303")).thenReturn(List.of());

        GlassesCandidateContextVO result = service.getContext("303").orElseThrow();

        assertEquals("NOT_STARTED", result.getInterviewStatus());
        assertEquals("保密", result.getGender());
        assertNull(result.getJobName());
        verify(jobService, never()).getDetail("job-2");
    }

    private boolean hasProperty(Class<?> type, String fieldName) {
        return java.util.Arrays.stream(type.getDeclaredFields())
                .anyMatch(field -> field.getName().equals(fieldName));
    }
}
