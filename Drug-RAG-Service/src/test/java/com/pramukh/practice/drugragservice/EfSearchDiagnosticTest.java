package com.pramukh.practice.drugragservice;

import org.junit.jupiter.api.Test;
import org.springframework.ai.embedding.EmbeddingModel;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import javax.sql.DataSource;
import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.Statement;

@SpringBootTest
class EfSearchDiagnosticTest {

    @Autowired
    private DataSource dataSource;

    @Autowired
    private EmbeddingModel embeddingModel;

    @Test
    void sameConnectionEfSearchComparison() throws Exception {
        float[] embedding = embeddingModel.embed("What is anxit used for?");
        StringBuilder vecLiteral = new StringBuilder("[");
        for (int i = 0; i < embedding.length; i++) {
            if (i > 0) vecLiteral.append(",");
            vecLiteral.append(embedding[i]);
        }
        vecLiteral.append("]");

        String sql = "SELECT metadata->>'drugName' AS drug_name, metadata->>'documentType' AS doc_type, " +
                "embedding <=> '" + vecLiteral + "'::vector AS distance " +
                "FROM drug_vector_store " +
                "WHERE metadata->>'drugName' = 'anxit 0.25mg tablet' AND metadata->>'documentType' = 'drug_knowledge' " +
                "ORDER BY embedding <=> '" + vecLiteral + "'::vector LIMIT 10";

        try (Connection conn = dataSource.getConnection(); Statement st = conn.createStatement()) {

            System.out.println("=== default hnsw.ef_search (session default) ===");
            try (ResultSet rs = st.executeQuery(sql)) {
                int count = 0;
                while (rs.next()) {
                    count++;
                    System.out.println("  FOUND: " + rs.getString("drug_name") + " / " + rs.getString("doc_type") + " dist=" + rs.getFloat("distance"));
                }
                System.out.println("Rows returned with default ef_search: " + count);
            }

            st.execute("SET hnsw.ef_search = 1000");
            System.out.println("=== hnsw.ef_search raised to 1000 on SAME connection ===");
            try (ResultSet rs = st.executeQuery(sql)) {
                int count = 0;
                while (rs.next()) {
                    count++;
                    System.out.println("  FOUND: " + rs.getString("drug_name") + " / " + rs.getString("doc_type") + " dist=" + rs.getFloat("distance"));
                }
                System.out.println("Rows returned with ef_search=1000: " + count);
            }
        }
    }
}
