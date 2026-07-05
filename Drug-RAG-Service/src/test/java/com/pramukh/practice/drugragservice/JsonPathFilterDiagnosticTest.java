package com.pramukh.practice.drugragservice;

import org.junit.jupiter.api.Test;
import org.springframework.ai.vectorstore.filter.Filter;
import org.springframework.ai.vectorstore.filter.FilterExpressionBuilder;
import org.springframework.ai.vectorstore.pgvector.PgVectorFilterExpressionConverter;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;

import java.util.List;
import java.util.Map;

@SpringBootTest
class JsonPathFilterDiagnosticTest {

    @Autowired
    private JdbcTemplate jdbcTemplate;

    @Test
    void showGeneratedJsonPathAndTestDirectly() {
        FilterExpressionBuilder b = new FilterExpressionBuilder();
        Filter.Expression expr = b.and(
                b.eq("drugName", "anxit 0.25mg tablet"),
                b.eq("documentType", "drug_knowledge")
        ).build();

        PgVectorFilterExpressionConverter converter = new PgVectorFilterExpressionConverter();
        String jsonPathFilter = converter.convertExpression(expr);
        System.out.println("=== Generated filter SQL fragment ===");
        System.out.println(jsonPathFilter);

        String sql = "SELECT count(*) FROM drug_vector_store WHERE " + jsonPathFilter;
        System.out.println("=== Full SQL ===");
        System.out.println(sql);

        Integer count = jdbcTemplate.queryForObject(sql, Integer.class);
        System.out.println("=== Row count matching jsonpath filter ===");
        System.out.println(count);

        System.out.println("=== Row count matching plain ->> equality (known-correct baseline) ===");
        Integer plainCount = jdbcTemplate.queryForObject(
                "SELECT count(*) FROM drug_vector_store WHERE metadata->>'drugName' = 'anxit 0.25mg tablet' AND metadata->>'documentType' = 'drug_knowledge'",
                Integer.class
        );
        System.out.println(plainCount);

        System.out.println("=== manual jsonpath test, hardcoded ===");
        List<Map<String, Object>> manual = jdbcTemplate.queryForList(
                "SELECT metadata FROM drug_vector_store WHERE metadata::jsonb @@ '$.drugName == \"anxit 0.25mg tablet\" && $.documentType == \"drug_knowledge\"'::jsonpath"
        );
        System.out.println("manual jsonpath rows: " + manual.size());
        for (Map<String, Object> row : manual) {
            System.out.println("  " + row);
        }
    }
}
