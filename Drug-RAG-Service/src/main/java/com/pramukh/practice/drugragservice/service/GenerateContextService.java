package com.pramukh.practice.drugragservice.service;

import com.pramukh.practice.drugragservice.DTO.DrugResolutionResult;
import com.pramukh.practice.drugragservice.entity.DrugMapping;
import com.pramukh.practice.drugragservice.repository.DrugRepository;
import org.springframework.ai.document.Document;
import org.springframework.ai.vectorstore.SearchRequest;
import org.springframework.ai.vectorstore.VectorStore;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class GenerateContextService {

    private final DrugRepository drugRepository;
    private final VectorStore vectorStore;

    public GenerateContextService(DrugRepository drugRepository, VectorStore vectorStore) {
        this.drugRepository = drugRepository;
        this.vectorStore = vectorStore;
    }

    public String getContext(DrugResolutionResult resolution, List<String> documentTypes, String question) {
        System.out.println("[CONTEXT-SERVICE] Step 3.1: Retrieving drug variants for: " + resolution.normalizedDrugName());
        if (resolution.specificFormulation()) {
            System.out.println("[CONTEXT-SERVICE] Step 3.1 Result: Using specific formulation");
            System.out.println("  - Formulation: " + resolution.matchedDrugName());
            return getContextByDrugName(resolution.matchedDrugName(), documentTypes, question);
        }
        List<DrugMapping> variants = drugRepository.findVariantsByNormalizedDrugName(resolution.normalizedDrugName());
        if (variants.isEmpty()) {
            throw new RuntimeException("No variants found for: " + resolution.normalizedDrugName());
        }
        DrugMapping primaryVariant = variants.get(0);
        System.out.println("[CONTEXT-SERVICE] Step 3.1 Result: Variants retrieved");
        System.out.println("  - Total Variants: " + variants.size());
        System.out.println("  - Primary Variant: " + primaryVariant.getDrugName());
        return getContextByDrugName(primaryVariant.getDrugName(), documentTypes, question);
    }

    private String getContextByDrugName(String drugName, List<String> documentTypes, String question) {
        StringBuilder contextBuilder = new StringBuilder();
        contextBuilder.append("Primary Drug Information:\n");
        contextBuilder.append("Primary Drug Name: ").append(drugName).append("\n\n");
        int stepCounter = 2;
        for (String docType : documentTypes) {
            System.out.println("[CONTEXT-SERVICE] Step 3." + stepCounter + ": Querying vector store (embeddings) for: " + drugName + " - " + docType);
            String filterExpression = "drugName == '" + drugName + "' && documentType == '" + docType + "'";
            System.out.println("Filter: " + filterExpression);
            SearchRequest searchRequest = SearchRequest.builder().query(question).topK(5).filterExpression(filterExpression).build();
            System.out.println(searchRequest.toString());
            List<Document> documents = vectorStore.similaritySearch(searchRequest);
            System.out.println("[CONTEXT-SERVICE] Step 3." + stepCounter + " Result: Retrieved " + documents.size() + " documents from embeddings");
            for (Document document : documents) {
                contextBuilder.append(document.getText());
                contextBuilder.append("\n\n");
            }
            stepCounter++;
        }
        System.out.println("[CONTEXT-SERVICE] Step 3 Complete: All context generated successfully");
        System.out.println(contextBuilder.toString());
        return contextBuilder.toString();
    }
}
