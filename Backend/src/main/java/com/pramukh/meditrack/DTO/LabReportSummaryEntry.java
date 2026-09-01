package com.pramukh.meditrack.DTO;

import lombok.Data;

import java.time.LocalDate;

@Data
public class LabReportSummaryEntry {
    private String testName;
    private String value;
    private String unit;
    private String referenceRange;
    private LocalDate recordedDate;
}
