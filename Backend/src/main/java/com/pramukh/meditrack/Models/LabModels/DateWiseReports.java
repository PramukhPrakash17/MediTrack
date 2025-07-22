package com.pramukh.meditrack.Models.LabModels;

import lombok.Data;

import java.time.Instant;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;

@Data
public class DateWiseReports {
    private LocalDate uploadDate;
    private List<LabReport> labReports = new ArrayList<>();
}
