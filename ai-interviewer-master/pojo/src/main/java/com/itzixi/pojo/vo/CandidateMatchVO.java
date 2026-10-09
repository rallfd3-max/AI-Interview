package com.itzixi.pojo.vo;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class CandidateMatchVO {

    private String candidateId;
    private String realName;
    private String mobileMasked;
    private Integer sex;
    private String email;
    private String jobId;
    private String jobName;
    private String school;
    private String major;
}
