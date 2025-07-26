package com.pramukh.meditrack.Models.LabModels;

import lombok.Data;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;

import java.util.ArrayList;
import java.util.List;

@Data
@Document(collection = "lab_data")
public class LabData {
    @Id
    private String insuranceNumber;
    private List<DateWiseReports> dateWiseReports = new ArrayList<>();
}




