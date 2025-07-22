package com.pramukh.meditrack.Models;

import lombok.Data;

import java.time.Instant;


@Data
public class LabReport {
    private String testName;
    private String value;
    private Instant uploadDate;
    private String unit;
    private String referenceRange;
}
