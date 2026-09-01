package com.pramukh.meditrack.DTO;

import lombok.Data;

import java.time.LocalDate;

@Data
public class NoteSummaryEntry {
    private String note;
    private LocalDate recordedDate;
}
