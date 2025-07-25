package com.pramukh.meditrack.DTO;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data

public class MedicineListDto {
     private List<MedicineDto> medicines;
}


