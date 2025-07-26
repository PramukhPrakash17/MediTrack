package com.pramukh.meditrack.Models.MedicineModel;

import lombok.Data;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;

import java.util.ArrayList;
import java.util.List;

@Data
@Document(collection = "medicalData")
public class MedicalData {
    @Id
    private String insuranceNumber;
    private List<DateWiseMedicine> dateWiseMedicines = new ArrayList<>();


}
