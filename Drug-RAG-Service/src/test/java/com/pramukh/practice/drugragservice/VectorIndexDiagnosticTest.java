package com.pramukh.practice.drugragservice;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;

import java.util.List;
import java.util.Map;

@SpringBootTest
class VectorIndexDiagnosticTest {

    @Autowired
    private JdbcTemplate jdbcTemplate;

    @Test
    void dropHnswIndexIfPresent() {
        jdbcTemplate.execute("DROP INDEX IF EXISTS drug_vector_store_index");
        System.out.println("=== HNSW index dropped (if it existed) ===");
        List<Map<String, Object>> idx = jdbcTemplate.queryForList(
                "SELECT indexname FROM pg_indexes WHERE tablename = 'drug_vector_store'"
        );
        idx.forEach(row -> System.out.println("REMAINING INDEX: " + row.get("indexname")));
    }

    @Test
    void inspectIndexAndSettings() {
        System.out.println("=== indexes on drug_vector_store ===");
        List<Map<String, Object>> idx = jdbcTemplate.queryForList(
                "SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'drug_vector_store'"
        );
        for (Map<String, Object> row : idx) {
            System.out.println(row.get("indexname") + " -> " + row.get("indexdef"));
        }

        System.out.println("=== row count ===");
        System.out.println(jdbcTemplate.queryForObject("SELECT count(*) FROM drug_vector_store", Integer.class));

        System.out.println("=== hnsw.ef_search / ivfflat.probes ===");
        try {
            System.out.println(jdbcTemplate.queryForObject("SHOW hnsw.ef_search", String.class));
        } catch (Exception e) {
            System.out.println("hnsw.ef_search not applicable: " + e.getMessage());
        }
        try {
            System.out.println(jdbcTemplate.queryForObject("SHOW ivfflat.probes", String.class));
        } catch (Exception e) {
            System.out.println("ivfflat.probes not applicable: " + e.getMessage());
        }

        System.out.println("=== EXPLAIN for filtered query ===");
        List<Map<String, Object>> plan = jdbcTemplate.queryForList(
                "EXPLAIN SELECT * FROM drug_vector_store " +
                        "WHERE metadata->>'drugName' = 'anxit 0.25mg tablet' AND metadata->>'documentType' = 'drug_knowledge' " +
                        "ORDER BY embedding <=> (SELECT embedding FROM drug_vector_store WHERE metadata->>'drugName' = 'anxit 0.25mg tablet' LIMIT 1) LIMIT 10"
        );
        for (Map<String, Object> row : plan) {
            System.out.println(row.values().iterator().next());
        }
    }
}
