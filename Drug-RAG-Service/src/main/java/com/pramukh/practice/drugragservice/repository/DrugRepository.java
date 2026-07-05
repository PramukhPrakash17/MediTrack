package com.pramukh.practice.drugragservice.repository;

import com.pramukh.practice.drugragservice.entity.DrugMapping;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;

public interface DrugRepository extends JpaRepository<DrugMapping, Long> {

    @Query(value = """
            SELECT *
            FROM drug_mapping d
            WHERE LOWER(REPLACE(d.drug_name, ' ', '')) =
                  LOWER(REPLACE(:drugName, ' ', ''))
            ORDER BY d.drug_name
            """, nativeQuery = true)
    List<DrugMapping> findDrugNameMatch(@Param("drugName") String drugName);

    @Query("""
        SELECT d
        FROM DrugMapping d
        WHERE LOWER(REPLACE(REPLACE(d.normalizedDrugName, ' ', ''), '/', '')) =
              LOWER(REPLACE(REPLACE(:drugName, ' ', ''), '/', ''))
        ORDER BY d.drugName
        """)
    List<DrugMapping> findNormalizedDrugMatch(@Param("drugName") String drugName);

    @Query(value = """
            SELECT *
            FROM drug_mapping d
            WHERE LOWER(d.drug_name) LIKE LOWER(CONCAT(:drugName, '%'))
            ORDER BY d.drug_name
            """, nativeQuery = true)
    List<DrugMapping> findFallbackMatch(@Param("drugName") String drugName);

    @Query(value = """
            SELECT DISTINCT *
            FROM drug_mapping d
            WHERE LOWER(d.normalized_drug_name) = LOWER(:normalizedDrugName)
            ORDER BY d.drug_name
            """, nativeQuery = true)
    List<DrugMapping> findVariantsByNormalizedDrugName(
            @Param("normalizedDrugName") String normalizedDrugName
    );
}