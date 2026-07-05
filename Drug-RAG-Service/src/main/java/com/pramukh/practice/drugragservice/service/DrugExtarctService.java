package com.pramukh.practice.drugragservice.service;


import com.pramukh.practice.drugragservice.DTO.DrugAgenticRouterDto;
import com.pramukh.practice.drugragservice.repository.DrugRepository;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.openai.OpenAiChatOptions;
import org.springframework.ai.vectorstore.VectorStore;
import org.springframework.stereotype.Service;

@Service
public class DrugExtarctService {

    private final ChatClient chatClient;
    public DrugExtarctService(ChatClient.Builder chatClient) {
        this.chatClient = chatClient.build();
    }

    public DrugAgenticRouterDto extract(String question) {
        System.out.println("[EXTRACT-SERVICE] Step 1.1: Processing question to extract drug name and document types");
        String prompt = """
        Extract:

        1. Drug Name
        2. Required document types

        Possible document types:
        - drug_knowledge
        - patient_support

        Rules:
        - Extract the drug name exactly as written in the doctor's question.
        - The extracted drug name must appear in the doctor's question.
        - Do NOT correct spelling, normalize, rewrite, translate, or guess the drug name.
        - Preserve numbers, units, symbols, and formulation words exactly as written.
        - Return ONLY the minimum required document types.
        - drug_knowledge: uses, side effects, substitutes, therapeutic/action/chemical class, habit forming.
        - patient_support: pregnancy, breastfeeding, alcohol, food, driving, kidney, liver, age, gender, dosage, consumption.
        - Return BOTH only if the question explicitly requires information from both datasets.
        - Never return unnecessary document types.
        - Return JSON only.

        Doctor Question:
        """ + question;
        DrugAgenticRouterDto response = chatClient.prompt().options(OpenAiChatOptions.builder().model("llama-3.1-8b-instant").temperature(0.0).build()).user(prompt).call().entity(DrugAgenticRouterDto.class);
        System.out.println("[EXTRACT-SERVICE] Step 1.1 Result: Extraction successful");
        System.out.println("  - Drug Name: " + response.getDrugName());
        System.out.println("  - Document Types: " + response.getDocumentType());
        return response;

    }
}
