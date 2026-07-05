package com.pramukh.practice.rag.Service;

import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.document.Document;
import org.springframework.ai.vectorstore.SearchRequest;
import org.springframework.ai.vectorstore.VectorStore;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class RagService {
    private final VectorStore vectorStore;
    private final ChatClient chatClient;

    public RagService(VectorStore vectorStore,  ChatClient.Builder chatClientBuilder) {
        this.vectorStore = vectorStore;
        this.chatClient = chatClientBuilder.build();
    }

    public String getAnswer(String question) {
        long ToatlTimeStart = System.nanoTime();

        long searchTimeStart = System.nanoTime();
        SearchRequest searchRequest = SearchRequest.builder().query(question).topK(5).build();
        List<Document> documents = vectorStore.similaritySearch(searchRequest);
        long searchTimeEnd = System.nanoTime();

        long contextStart = System.nanoTime();
        StringBuilder contextBuilder = new StringBuilder();
        for (Document document : documents) {
            contextBuilder.append(document.getText());
            contextBuilder.append("\n\n");
        }
        String context = contextBuilder.toString();

        String prompt =
                """
                You are an AI-powered clinical assistant chatbot.
        
                Use ONLY the provided medical context.
        
                Analyze the patient's symptoms and provide a concise clinical-style response.
        
                Follow this format STRICTLY:
        
                Clinical Observation:
                - short observation 1
                - short observation 2
        
                Most Likely Condition:
                - disease name
        
                Why this condition matches:
                - short reason 1
                - short reason 2
        
                Possible Causes:
                - cause 1
                - cause 2
        
                IMPORTANT RULES:
                - Include "Suggested Medications" section ONLY if medication information is explicitly present in the context.
                - If medication information is not present, completely omit that section.
                - Never write:
                  "None specified"
                  "Not mentioned"
                  "No medication available"
                - Keep the response concise and professional.
                - Avoid repeating the same information.
                - Do not generate unnecessary explanations.
                - End with a short clinical recommendation.
        
                Context:
                """ + context +

                        """
                
                        Patient Symptoms:
                        """ + question;

        long contextEnd = System.nanoTime();

        long llmStart = System.nanoTime();

        String answer = chatClient.prompt().user(prompt).call().content();

        long llmend = System.nanoTime();

        long totalEnd = System.nanoTime();


        System.out.println("========== RAG PERFORMANCE ==========");
        System.out.println("Vector search time: " + toMs(searchTimeEnd - searchTimeStart) + " ms");
        System.out.println("Prompt/context build time: " + toMs(contextEnd - contextStart) + " ms");
        System.out.println("LLM generation time: " + toMs(llmend - llmStart) + " ms");
        System.out.println("Total request time: " + toMs(totalEnd - ToatlTimeStart) + " ms");
        System.out.println("Retrieved chunks: " + documents.size());
        System.out.println("=====================================");
        return answer;
    }

    private long toMs(long nanoTime) {
        return nanoTime / 1_000_000;
    }

}
