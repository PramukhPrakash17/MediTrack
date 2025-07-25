package com.pramukh.meditrack.Models.NotesModels;

import lombok.Data;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;

@Data
public class DateWiseNotes {
    private LocalDate date;
    private List<String> doctornotes = new ArrayList<>();
}
