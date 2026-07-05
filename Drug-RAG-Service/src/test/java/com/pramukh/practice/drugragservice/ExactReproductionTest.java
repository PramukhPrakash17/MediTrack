package com.pramukh.practice.drugragservice;

import com.pgvector.PGvector;
import org.junit.jupiter.api.Test;
import org.springframework.ai.embedding.EmbeddingModel;
import org.springframework.ai.vectorstore.filter.Filter;
import org.springframework.ai.vectorstore.filter.FilterExpressionBuilder;
import org.springframework.ai.vectorstore.pgvector.PgVectorFilterExpressionConverter;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import javax.sql.DataSource;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;

@SpringBootTest
class ExactReproductionTest {

    @Autowired
    private DataSource dataSource;

    @Autowired
    private EmbeddingModel embeddingModel;

    @Test
    void reproduceExactPgVectorStoreQuery() throws Exception {
        FilterExpressionBuilder b = new FilterExpressionBuilder();
        Filter.Expression expr = b.and(
                b.eq("drugName", "anxit 0.25mg tablet"),
                b.eq("documentType", "drug_knowledge")
        ).build();
        String jsonPathFilter = new PgVectorFilterExpressionConverter().convertExpression(expr);

        float[] embedding = embeddingModel.embed("What is anxit used for?");
        PGvector vec = new PGvector(embedding);
        double distanceThreshold = 1 - 0.0; // SearchRequest default similarityThreshold = 0.0

        String jsonPathSql = "SELECT *, embedding <=> ? AS distance FROM drug_vector_store WHERE embedding <=> ? < ? AND " + jsonPathFilter + " ORDER BY distance LIMIT ?";
        System.out.println("=== jsonpath filter + bind-param vector ===");
        run(jsonPathSql, vec, distanceThreshold);

        String plainFilter = "metadata->>'drugName' = 'anxit 0.25mg tablet' AND metadata->>'documentType' = 'drug_knowledge'";
        String plainSql = "SELECT *, embedding <=> ? AS distance FROM drug_vector_store WHERE embedding <=> ? < ? AND " + plainFilter + " ORDER BY distance LIMIT ?";
        System.out.println("=== plain ->> filter + bind-param vector (ablation) ===");
        run(plainSql, vec, distanceThreshold);

        System.out.println("=== EXPLAIN: jsonpath version ===");
        explain(jsonPathSql, vec, distanceThreshold);

        System.out.println("=== EXPLAIN: plain ->> version ===");
        explain(plainSql, vec, distanceThreshold);

        System.out.println("=== jsonpath version with hnsw.ef_search=1000 ===");
        try (Connection conn = dataSource.getConnection()) {
            try (PreparedStatement setEf = conn.prepareStatement("SET hnsw.ef_search = 1000")) {
                setEf.execute();
            }
            try (PreparedStatement ps = conn.prepareStatement(jsonPathSql)) {
                ps.setObject(1, vec);
                ps.setObject(2, vec);
                ps.setDouble(3, distanceThreshold);
                ps.setInt(4, 5);
                try (ResultSet rs = ps.executeQuery()) {
                    int count = 0;
                    while (rs.next()) {
                        count++;
                        System.out.println("FOUND row, distance=" + rs.getDouble("distance"));
                    }
                    System.out.println("=== row count with ef_search=1000: " + count + " ===");
                }
            }
        }
    }

    private void explain(String sql, PGvector vec, double distanceThreshold) throws Exception {
        try (Connection conn = dataSource.getConnection();
             PreparedStatement ps = conn.prepareStatement("EXPLAIN " + sql)) {
            ps.setObject(1, vec);
            ps.setObject(2, vec);
            ps.setDouble(3, distanceThreshold);
            ps.setInt(4, 5);
            try (ResultSet rs = ps.executeQuery()) {
                while (rs.next()) {
                    System.out.println(rs.getString(1));
                }
            }
        }
    }

    private void run(String sql, PGvector vec, double distanceThreshold) throws Exception {
        System.out.println("SQL: " + sql);
        try (Connection conn = dataSource.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setObject(1, vec);
            ps.setObject(2, vec);
            ps.setDouble(3, distanceThreshold);
            ps.setInt(4, 5);

            try (ResultSet rs = ps.executeQuery()) {
                int count = 0;
                while (rs.next()) {
                    count++;
                    System.out.println("FOUND row, distance=" + rs.getDouble("distance"));
                }
                System.out.println("=== row count: " + count + " ===");
            }
        }
    }
}
