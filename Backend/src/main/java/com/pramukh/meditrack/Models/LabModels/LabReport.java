package com.pramukh.meditrack.Models.LabModels;

import lombok.Data;

@Data
public class LabReport {
    private String testName;
    private String value;
    private String unit;
    private String referenceRange;
}
