package com.pramukh.practice.drugragservice;

import com.pramukh.practice.drugragservice.DTO.DrugAgenticRouterDto;
import com.pramukh.practice.drugragservice.DTO.DrugResolutionResult;
import com.pramukh.practice.drugragservice.entity.DrugMapping;
import com.pramukh.practice.drugragservice.repository.DrugRepository;
import com.pramukh.practice.drugragservice.service.DrugExtarctService;
import com.pramukh.practice.drugragservice.service.DrugResolveService;
import org.junit.jupiter.api.Test;
import org.springframework.ai.document.Document;
import org.springframework.ai.vectorstore.SearchRequest;
import org.springframework.ai.vectorstore.VectorStore;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * Walks the same four-step pipeline DrugRagService.getAnswers() runs for
 * "What is anxit used for?", asserting at each step so the exact failing
 * step is pinpointed instead of only observing the final answer.
 */
@SpringBootTest
class AnxitPipelineFlowTest {

    private static final String QUESTION = "What is anxit used for?";

    @Autowired
    private DrugExtarctService drugExtarctService;

    @Autowired
    private DrugResolveService drugResolveService;

    @Autowired
    private DrugRepository drugRepository;

    @Autowired
    private VectorStore vectorStore;

    @Test
    void walkPipelineAndPinpointFailure() {

        // ---- Step 1: extract drug name + required document types (LLM) ----
        DrugAgenticRouterDto extraction = drugExtarctService.extract(QUESTION);
        System.out.println("STEP 1 -> drug=" + extraction.getDrugName() + " docTypes=" + extraction.getDocumentType());
        assertEquals("anxit", extraction.getDrugName().toLowerCase());
        assertTrue(extraction.getDocumentType().contains("drug_knowledge"));

        // ---- Step 2: resolve drug name against drug_mapping (DB only) ----
        DrugResolutionResult resolution = drugResolveService.resolveDrug(extraction.getDrugName());
        System.out.println("STEP 2 -> normalizedDrugName=" + resolution.normalizedDrugName()
                + " matchedDrugName=" + resolution.matchedDrugName()
                + " specificFormulation=" + resolution.specificFormulation());
        assertEquals("anxit", resolution.normalizedDrugName());
        assertFalse(resolution.specificFormulation(), "bare 'anxit' should not resolve to one specific formulation");

        // ---- Step 3.1: fetch variants, pick primary (DB only) ----
        List<DrugMapping> variants = drugRepository.findVariantsByNormalizedDrugName(resolution.normalizedDrugName());
        assertFalse(variants.isEmpty(), "expected at least one variant for 'anxit'");
        String primaryVariant = variants.get(0).getDrugName();
        System.out.println("STEP 3.1 -> variants=" + variants.size() + " primaryVariant=" + primaryVariant);
        assertEquals("anxit 0.25mg tablet", primaryVariant);

        // ---- Step 3.2: vector search for the primary variant + drug_knowledge (this is where the bug lives) ----
        String filterExpression = "drugName == '" + primaryVariant + "' && documentType == 'drug_knowledge'";
        SearchRequest searchRequest = SearchRequest.builder()
                .query(QUESTION)
                .topK(5)
                .filterExpression(filterExpression)
                .build();
        List<Document> documents = vectorStore.similaritySearch(searchRequest);
        System.out.println("STEP 3.2 -> filter=" + filterExpression + " retrieved=" + documents.size() + " documents");
        for (Document d : documents) {
            System.out.println("    " + d.getMetadata());
        }

        assertFalse(documents.isEmpty(),
                "Step 3.2 (vector retrieval) returned 0 documents for a drugName+documentType combo that "
                        + "definitely exists in drug_vector_store. Root cause: PgVectorFilterExpressionConverter "
                        + "builds a 'metadata::jsonb @@ jsonpath' predicate, which Postgres cannot cost-estimate. "
                        + "Combined with the HNSW index on `embedding`, the planner runs the ANN index scan first "
                        + "(bounded by hnsw.ef_search, default 40) and applies the filter only to that candidate "
                        + "set, silently dropping matches outside the top ~40 nearest neighbors. Fix: set "
                        + "spring.datasource.hikari.connection-init-sql=SET hnsw.ef_search = 500 (or higher) in "
                        + "application.properties.");
    }
}
