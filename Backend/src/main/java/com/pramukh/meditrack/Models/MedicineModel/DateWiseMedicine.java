package com.pramukh.meditrack.Models.MedicineModel;

import lombok.Data;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;

@Data
public class DateWiseMedicine {
    private LocalDate date;
    private List<Medicine> medicines = new ArrayList<>();
}
