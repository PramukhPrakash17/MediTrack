package com.pramukh.practice.drugragservice.service;

import org.springaicommunity.mcp.annotation.McpTool;
import org.springframework.stereotype.Component;

@Component
public class DrugMcpTool {

    private final DrugRagService drugRagService;

    public DrugMcpTool(DrugRagService drugRagService) {
        this.drugRagService = drugRagService;
    }


    @McpTool(name = "drug_information", description = "Analyze medication-related questions using the MediTrack Drug RAG knowledge base.\n" + "\n" + "Use this tool whenever the doctor asks about a medication, including its uses, indications, side effects, contraindications, dosage guidance, pregnancy safety, alcohol interactions, drug substitutions, therapeutic class, patient suitability, or whether a specific medication is appropriate for a patient's condition.\n" + "\n" + "Pass the doctor's complete natural-language question unchanged. The tool will retrieve relevant drug information from the MediTrack Drug RAG knowledge base and provide an evidence-based response using only the retrieved information.\n" + "\n" + "Do not use this tool for identifying diseases based on symptoms, providing differential diagnoses, or analyzing X-ray images. Those requests should be handled by their respective tools.\n")
    public String drugInformation(String question) {
        return drugRagService.getAnswers(question);
    }

}
