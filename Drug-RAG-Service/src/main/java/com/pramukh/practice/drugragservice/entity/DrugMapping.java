package com.pramukh.practice.drugragservice.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Entity
@Table(name = "drug_mapping")
@Getter
@Setter
@NoArgsConstructor
public class DrugMapping {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    @Column(name = "drug_name")
    private String drugName;
    @Column(name = "normalized_drug_name")
    private String normalizedDrugName;


    public DrugMapping(String drugName, String normalizedDrugName) {
        this.drugName = drugName;
        this.normalizedDrugName = normalizedDrugName;
    }
}
