package com.pramukh.meditrack.Models;

import lombok.Data;

import java.time.Instant;
import java.time.LocalDate;

@Data
public class Medicine {
    private String name;
    private String dosage;
    private LocalDate startDate;
    private LocalDate endDate;
    private Instant prescribedAt;
}
