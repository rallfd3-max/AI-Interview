package com.itzixi.pojo.vo;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class CandidateMatchResultVO {

    private String queryName;
    private Integer matchedCount;
    private List<CandidateMatchVO> candidates;
}
