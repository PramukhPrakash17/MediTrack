package com.pramukh.practice.drugragservice;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;

import java.util.List;
import java.util.Map;

@SpringBootTest
class DrugNameMismatchDiagnosticTest {

    @Autowired
    private JdbcTemplate jdbcTemplate;

    @Test
    void compareDrugNameStrings() {
        System.out.println("=== drug_vector_store rows for normalizedDrugName=anxit ===");
        List<Map<String, Object>> vsRows = jdbcTemplate.queryForList(
                "SELECT metadata->>'drugName' AS drug_name, metadata->>'documentType' AS doc_type, " +
                        "length(metadata->>'drugName') AS len, encode(sha256((metadata->>'drugName')::bytea), 'hex') AS hash " +
                        "FROM drug_vector_store WHERE metadata->>'normalizedDrugName' = 'anxit'"
        );
        for (Map<String, Object> row : vsRows) {
            System.out.println("VS: [" + row.get("drug_name") + "] len=" + row.get("len") + " docType=[" + row.get("doc_type") + "] hash=" + row.get("hash"));
        }

        System.out.println("=== drug_mapping rows for normalized_drug_name=anxit ===");
        List<Map<String, Object>> mapRows = jdbcTemplate.queryForList(
                "SELECT drug_name, length(drug_name) AS len, encode(sha256(drug_name::bytea), 'hex') AS hash " +
                        "FROM drug_mapping WHERE normalized_drug_name = 'anxit' ORDER BY drug_name"
        );
        for (Map<String, Object> row : mapRows) {
            System.out.println("MAP: [" + row.get("drug_name") + "] len=" + row.get("len") + " hash=" + row.get("hash"));
        }

        System.out.println("=== distinct documentType values present for anxit rows ===");
        List<Map<String, Object>> docTypes = jdbcTemplate.queryForList(
                "SELECT DISTINCT metadata->>'documentType' AS doc_type FROM drug_vector_store WHERE metadata->>'normalizedDrugName' = 'anxit'"
        );
        for (Map<String, Object> row : docTypes) {
            System.out.println("DOC_TYPE: [" + row.get("doc_type") + "]");
        }
    }
}
