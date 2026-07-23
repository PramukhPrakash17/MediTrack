package com.pramukh.practice.drugragservice.service;

import com.pramukh.practice.drugragservice.DTO.DrugAgenticRouterDto;
import com.pramukh.practice.drugragservice.DTO.DrugResolutionResult;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.openai.OpenAiChatOptions;
import org.springframework.stereotype.Service;

import java.sql.SQLOutput;
import java.util.List;


@Service
public class DrugRagService {


    private final ChatClient chatClient;
    private final DrugExtarctService drugExtarctService;
    private final DrugResolveService drugResolveService;
    private final GenerateContextService contextService;

    public DrugRagService(ChatClient.Builder chatClientBuilder, DrugExtarctService drugExtarctService, DrugResolveService drugResolveService, GenerateContextService contextService) {

        this.chatClient = chatClientBuilder.build();
        this.drugExtarctService = drugExtarctService;
        this.drugResolveService = drugResolveService;
        this.contextService = contextService;
    }

    public String getAnswers(String question) {
        System.out.println("[RAG-SERVICE] Step 1: Extracting drug name and document types from question");
        DrugAgenticRouterDto response = drugExtarctService.extract(question);
        String drug = response.getDrugName();
        List<String> documentType = response.getDocumentType();
        System.out.println("[RAG-SERVICE] Step 1 Result: Extraction complete");
        System.out.println("  - Extracted Drug: " + drug);
        System.out.println("  - Document Types: " + documentType);

        System.out.println("[RAG-SERVICE] Step 2: Resolving drug in database");
        DrugResolutionResult drugResolutionResult;
        try {
            drugResolutionResult = drugResolveService.resolveDrug(drug);
            System.out.println("[RAG-SERVICE] Step 2 Result: Drug resolution complete");
            System.out.println("  - Normalized Drug Name: " + drugResolutionResult.normalizedDrugName());
            System.out.println("  - Matched Drug Name: " + drugResolutionResult.matchedDrugName());
        } catch (RuntimeException e) {
            System.out.println("[RAG-SERVICE] Step 2 Result: Drug resolution failed");
            System.out.println("  - Error: Drug not found in database: " + drug);
            return "The drug name '" + drug + "' was not found in the available drug dataset. " + "Please check the spelling or enter a valid medicine name.";
        }

        System.out.println("[RAG-SERVICE] Step 3: Building context from vector store and database");
        String context = contextService.getContext(drugResolutionResult, documentType, question);
        System.out.println("[RAG-SERVICE] Step 3 Result: Context build complete");

        System.out.println("[RAG-SERVICE] Step 4: Calling LLM to generate response");
        String prompt = """
                You are a dataset-grounded clinical drug assistant.
                
                Answer the doctor's question using ONLY the retrieved drug context.
                
                Retrieved Drug Context:
                """ + context + """
                
                RULES:
                - Use ONLY the retrieved drug context. Do not use outside medical knowledge, inference, assumptions, or unsupported additions (such as symptoms, mechanisms, dosage, precautions, recommendations, or examples).
                - Convert the retrieved information into complete, natural, professional sentences while preserving the original meaning.
                - Preserve the terminology used in the retrieved context wherever appropriate.
                - Do not introduce new medical facts or explanations.
                - If the requested information is not available in the retrieved context, reply exactly:
                  "This information is not available in the dataset."
                - Answer only what the doctor asked using ONLY the "Primary Drug Information" section.
                - Do not mention the dataset or retrieved context in the response.
                
                STYLE:
                - Professional, concise, and doctor-facing.
                - Write naturally as a clinical assistant rather than repeating raw dataset values.
                - Expand short dataset values into readable sentences without changing their meaning.
                - Avoid repetitive openings such as "According to the retrieved information."
                
                Example 1
                
                Context:
                Primary Drug Information:
                Drug Name: Alex Syrup
                Uses: Treatment of Cough.
                
                Response:
                The primary use of Alex Syrup is the treatment of cough.
                
                Example 2
                
                Context:
                Primary Drug Information:
                Drug Name: YPO 2 mg Syrup
                Uses: Treatment of Cough.
                Substitutes: Corex D Syrup, Benadryl Cough Syrup.
                
                Response:
                The primary use of YPO 2 mg Syrup is the treatment of cough. The available substitutes are Corex D Syrup and Benadryl Cough Syrup.
                
                Example 3
                
                Context:
                Primary Drug Information:
                Drug Name: Avil Tablet
                Side Effects: Sleepiness, Dry mouth, Dizziness.
                
                Response:
                The commonly reported side effects of Avil Tablet include sleepiness, dry mouth, and dizziness.
                
                Doctor Question:
                """ + question;
        String answer = chatClient.prompt().options(OpenAiChatOptions.builder().model("llama-3.1-8b-instant").temperature(0.2).build()).user(prompt).call().content();
        System.out.println("[RAG-SERVICE] Step 4 Result: LLM response generated");
        System.out.println("  - Response Length: " + answer.length() + " characters");
        System.out.println("[RAG-SERVICE] Returning to controller");
        return answer;

    }


}
