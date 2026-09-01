package com.pramukh.practice.rag.Service;

import org.springframework.ai.mcp.annotation.McpTool;
import org.springframework.ai.mcp.annotation.McpToolParam;
import org.springframework.stereotype.Component;

@Component
public class SymptomsMcpTool {

    private final RagService ragService;

    public SymptomsMcpTool(RagService ragService) {
        this.ragService = ragService;
    }

    @McpTool(name = "diagnose_patient", description = "Analyze patient symptoms described in natural language and identify possible medical conditions using the MediTrack Symptoms RAG knowledge base.")
    public String diagnosePatient(@McpToolParam(description = "The doctor's complete natural-language question describing the patient's symptoms.", required = true) String question) {
        return ragService.getAnswer(question);
    }
}
