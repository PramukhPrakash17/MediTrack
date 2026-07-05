package com.pramukh.practice.drugragservice.DTO;

import lombok.Getter;
import lombok.Setter;

import java.util.List;

@Getter
@Setter
public class DrugAgenticRouterDto {
    private String drugName;
    private List<String> documentType;
}
