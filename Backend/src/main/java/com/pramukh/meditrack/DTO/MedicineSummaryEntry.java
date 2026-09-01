package com.pramukh.meditrack.DTO;

import lombok.Data;

import java.time.LocalDate;

@Data
public class MedicineSummaryEntry {
    private String name;
    private String dosage;
    private String frequency;
    private LocalDate startDate;
    private LocalDate endDate;
    private String instructions;
    private LocalDate recordedDate;
}
