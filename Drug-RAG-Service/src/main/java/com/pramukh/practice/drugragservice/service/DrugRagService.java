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
        - Use ONLY the retrieved context. No outside medical knowledge, inference, or unsupported additions (symptoms, mechanisms, dosage, precautions, recommendations, examples).
        - Rephrasing into professional clinical sentences is allowed, without changing meaning.
        - If the requested info isn't in the context, reply exactly: "This information is not available in the dataset."
        - Answer only what was asked, using ONLY the "Primary Drug Information" section. Never combine multiple variants' data.
        - "Substitutes" inside Primary Drug Information are different drugs, NOT other variants - never relabel them as such.
        - Only a separate, literal "Other Available Variants:" heading in the context counts as that section; nothing inside Primary Drug Information (including Substitutes) does.

        OUTPUT FORMAT:
        1. Answer using ONLY Primary Drug Information.
        2. If a separate "Other Available Variants:" heading exists in the context, append it after your answer under the heading "Other available variants:", copying names exactly with no commentary. Otherwise, omit this section entirely - even if Substitutes are mentioned.

        STYLE:
        - Concise, professional, doctor-facing tone. Rephrase dataset values into full sentences without adding new information.

        Example 1

        Context:
        Primary Drug Information:
        Drug name: avil 25 tablet.
        Uses: Treatment of Allergic conditions.

        Other Available Variants:
        - avil 50mg tablet
        - avil injection

        Response:
        According to the retrieved information, the primary use of Avil is the treatment of allergic conditions.

        Other available variants:
        - avil 50mg tablet
        - avil injection

        Example 2

        Context:
        Primary Drug Information:
        Drug name: alex syrup.
        Uses: Treatment of Cough.

        Response:
        According to the retrieved information, the primary use of Alex Syrup is the treatment of cough.

        Example 3

        Context:
        Primary Drug Information:
        Drug name: ypo 2mg syrup.
        Uses: Treatment of Cough.
        Substitutes: Corex D Syrup, Benadryl Cough Syrup.

        Response:
        According to the retrieved information, the primary use of Ypo Syrup is the treatment of cough.

        Doctor Question:
        """ + question;
        String answer = chatClient.prompt().options(OpenAiChatOptions.builder().model("llama-3.1-8b-instant").temperature(0.2).build()).user(prompt).call().content();
        System.out.println("[RAG-SERVICE] Step 4 Result: LLM response generated");
        System.out.println("  - Response Length: " + answer.length() + " characters");
        System.out.println("[RAG-SERVICE] Returning to controller");
        return answer;

    }


}
