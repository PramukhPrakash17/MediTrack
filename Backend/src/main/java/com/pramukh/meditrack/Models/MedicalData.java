package com.pramukh.meditrack.Models;

import org.springframework.data.annotation.Id;
import lombok.Data;
import org.springframework.data.mongodb.core.mapping.Document;

import java.util.ArrayList;
import java.util.List;

@Data
@Document(collection = "medicine_history")
public class MedicalData {
    @Id
    private String insuranceNumber;
    private List<Medicine> medicines = new ArrayList<>();
}
