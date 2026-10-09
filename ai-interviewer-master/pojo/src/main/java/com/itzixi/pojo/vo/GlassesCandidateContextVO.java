package com.itzixi.pojo.vo;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * Candidate information that is safe and useful for the smart-glasses display.
 * Deliberately excludes identity number, mobile number, address, email and media URLs.
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class GlassesCandidateContextVO {

    private String candidateId;
    private String realName;
    private String gender;
    private String school;
    private String major;
    private String jobId;
    private String jobName;
    private String jobDescriptionSummary;
    private String candidateProfile;
    private String experienceSummary;
    private String interviewStatus;
    private String latestInterviewSummary;
    private String latestInterviewScore;
}
