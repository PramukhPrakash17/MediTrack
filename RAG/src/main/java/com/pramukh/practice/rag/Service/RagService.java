package com.pramukh.practice.rag.Service;

import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.document.Document;
import org.springframework.ai.vectorstore.SearchRequest;
import org.springframework.ai.vectorstore.VectorStore;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class RagService {

    private static final int TOP_K = 8;
    private static final double SIMILARITY_THRESHOLD = 0.55;

    private final VectorStore vectorStore;
    private final ChatClient chatClient;

    public RagService(VectorStore vectorStore, ChatClient.Builder chatClientBuilder) {
        this.vectorStore = vectorStore;
        this.chatClient = chatClientBuilder.build();
    }

    public String getAnswer(String question) {

        long totalTimeStart = System.nanoTime();

        /*
         * Convert the user's question into a better retrieval query.
         *
         * Example:
         * "What are the symptoms of varicose veins?"
         *
         * becomes:
         * "What are the symptoms of varicose veins?
         * symptoms signs clinical manifestations"
         */
        String retrievalQuery = buildRetrievalQuery(question);

        long searchTimeStart = System.nanoTime();

        SearchRequest searchRequest = SearchRequest.builder().query(retrievalQuery).topK(TOP_K).similarityThreshold(SIMILARITY_THRESHOLD).build();

        List<Document> documents = vectorStore.similaritySearch(searchRequest);

        long searchTimeEnd = System.nanoTime();

        /*
         * Do not call the LLM when no relevant PDF chunks were found.
         */
        if (documents == null || documents.isEmpty()) {
            return "The provided PDF context does not contain enough information to answer this question.";
        }

        long contextStart = System.nanoTime();

        String context = buildContext(documents);

        String prompt =
                """
                You are a medical PDF assistant.
        
                Answer the user's question using ONLY the provided PDF context.
        
                Rules:
                - Use ONLY the provided PDF context to answer the question.
                - Do not use outside knowledge or invent any information.
                - If the answer is not present in the provided context, reply exactly:
                  "The provided PDF context does not contain enough information to answer this question."
                - Answer naturally based on the retrieved context.
                - Preserve the wording of the PDF wherever possible.
                - Do not unnecessarily paraphrase or rewrite the information.
                - Combine information from multiple retrieved sections only when needed to fully answer the question.
                - Include only information relevant to the user's question.
                - Keep the answer concise (2–4 sentences unless more detail is requested).
                - Do not add assumptions, explanations, or medical advice that are not explicitly present in the context.
                - Mention medications or treatments only if they are explicitly present in the retrieved context.
                - Do not use headings, bullet points, markdown, or additional sections.
                - Do not mention the PDF or say phrases such as "According to the PDF" or "Based on the provided context."
        
                PDF Context:
                %s
        
                User Question:
                %s
                """.formatted(context, question);

        long contextEnd = System.nanoTime();

        long llmStart = System.nanoTime();

        String answer = chatClient.prompt().user(prompt).call().content();

        long llmEnd = System.nanoTime();
        long totalEnd = System.nanoTime();

        System.out.println("========== RAG PERFORMANCE ==========");
        System.out.println("Original question: " + question);
        System.out.println("Retrieval query: " + retrievalQuery);
        System.out.println("Vector search time: " + toMs(searchTimeEnd - searchTimeStart) + " ms");
        System.out.println("Prompt/context build time: " + toMs(contextEnd - contextStart) + " ms");
        System.out.println("LLM generation time: " + toMs(llmEnd - llmStart) + " ms");
        System.out.println("Total request time: " + toMs(totalEnd - totalTimeStart) + " ms");
        System.out.println("Retrieved chunks: " + documents.size());
        System.out.println("=====================================");

        return answer;
    }

    /**
     * Expands the question with words commonly used in medical PDF sections.
     * This helps the vector search retrieve the correct section.
     */
    private String buildRetrievalQuery(String question) {

        String normalizedQuestion = question.toLowerCase();

        if (containsAny(normalizedQuestion, "symptom", "symptoms", "sign", "signs")) {
            return question + " symptoms signs clinical manifestations";
        }

        if (containsAny(normalizedQuestion, "cause", "causes", "caused", "reason", "risk factor", "risk factors")) {
            return question + " causes risk factors predisposing factors";
        }

        if (containsAny(normalizedQuestion, "treatment", "treat", "therapy", "medicine", "medication", "cure")) {
            return question + " treatment therapy medication symptom relief surgery";
        }

        if (containsAny(normalizedQuestion, "diagnosis", "diagnose", "test", "tests", "detected", "detect")) {
            return question + " diagnosis examination tests detection";
        }

        if (containsAny(normalizedQuestion, "prognosis", "outcome", "recovery")) {
            return question + " prognosis outcome recovery";
        }

        if (containsAny(normalizedQuestion, "what is", "what are", "definition", "define", "meaning")) {
            return question + " definition description";
        }

        return question;
    }

    /**
     * Checks whether the question contains at least one keyword.
     */
    private boolean containsAny(String text, String... keywords) {
        for (String keyword : keywords) {
            if (text.contains(keyword)) {
                return true;
            }
        }

        return false;
    }

    /**
     * Combines the retrieved PDF documents into one context.
     * Each retrieved chunk is kept separate.
     */
    private String buildContext(List<Document> documents) {

        StringBuilder contextBuilder = new StringBuilder();

        for (int index = 0; index < documents.size(); index++) {

            Document document = documents.get(index);

            contextBuilder.append("[Retrieved PDF Chunk ").append(index + 1).append("]\n");

            contextBuilder.append(document.getText());
            contextBuilder.append("\n\n");
        }

        return contextBuilder.toString();
    }

    private long toMs(long nanoTime) {
        return nanoTime / 1_000_000;
    }
}