package com.pramukh.practice.drugragservice.DTO;

public record DrugResolutionResult(String normalizedDrugName, String matchedDrugName, boolean specificFormulation) {
}
