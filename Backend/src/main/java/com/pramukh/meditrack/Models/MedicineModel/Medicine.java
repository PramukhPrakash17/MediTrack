package com.pramukh.meditrack.Models.MedicineModel;

import lombok.Data;

import java.time.Instant;
import java.time.LocalDate;

@Data
public class Medicine {
    private String name;
    private String dosage;
    private String frequency;
    private LocalDate startDate;
    private LocalDate endDate;
    private String instructions;
}
