package com.pramukh.practice.drugragservice;

import org.junit.jupiter.api.Test;
import org.springframework.ai.document.Document;
import org.springframework.ai.vectorstore.SearchRequest;
import org.springframework.ai.vectorstore.filter.Filter;
import org.springframework.ai.vectorstore.filter.FilterExpressionBuilder;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;

import java.util.List;

@SpringBootTest
class VectorStoreFilterDiagnosticTest {

    @Autowired
    private org.springframework.ai.vectorstore.VectorStore vectorStore;

    @Autowired
    private JdbcTemplate jdbcTemplate;

    @Test
    void diagnoseFiltersWithRaisedEfSearch() {
        jdbcTemplate.execute("SET hnsw.ef_search = 1000");
        System.out.println(">>> hnsw.ef_search raised to 1000 for this session <<<");

        report("combined AND (string filter) w/ ef_search=1000", SearchRequest.builder()
                .query("What is anxit used for?").topK(10)
                .filterExpression("drugName == 'anxit 0.25mg tablet' && documentType == 'drug_knowledge'").build());
    }

    @Test
    void diagnoseFilters() {
        report("no filter, generic query", SearchRequest.builder()
                .query("anxit").topK(10).build());

        report("documentType only (string filter)", SearchRequest.builder()
                .query("anxit").topK(10)
                .filterExpression("documentType == 'drug_knowledge'").build());

        report("drugName only (string filter)", SearchRequest.builder()
                .query("anxit").topK(10)
                .filterExpression("drugName == 'anxit 0.25mg tablet'").build());

        report("combined AND (string filter)", SearchRequest.builder()
                .query("anxit").topK(10)
                .filterExpression("drugName == 'anxit 0.25mg tablet' && documentType == 'drug_knowledge'").build());

        FilterExpressionBuilder b = new FilterExpressionBuilder();
        Filter.Expression builderExpr = b.and(
                b.eq("drugName", "anxit 0.25mg tablet"),
                b.eq("documentType", "drug_knowledge")
        ).build();
        report("combined AND (FilterExpressionBuilder, not string DSL)", SearchRequest.builder()
                .query("anxit").topK(10)
                .filterExpression(builderExpr).build());

        report("normalizedDrugName only", SearchRequest.builder()
                .query("anxit").topK(10)
                .filterExpression("normalizedDrugName == 'anxit'").build());
    }

    private void report(String label, SearchRequest request) {
        List<Document> docs = vectorStore.similaritySearch(request);
        System.out.println("### " + label + " -> " + docs.size() + " docs");
        for (Document d : docs) {
            System.out.println("    metadata=" + d.getMetadata());
        }
    }
}
