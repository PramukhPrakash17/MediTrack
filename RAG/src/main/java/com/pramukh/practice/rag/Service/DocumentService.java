package com.pramukh.practice.rag.Service;

import org.springframework.ai.document.Document;
import org.springframework.ai.reader.pdf.PagePdfDocumentReader;
import org.springframework.ai.reader.pdf.config.PdfDocumentReaderConfig;

import org.springframework.ai.transformer.splitter.TokenTextSplitter;
import org.springframework.ai.vectorstore.VectorStore;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.Resource;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;

@Service
public class DocumentService {
    @Value("classpath:/pdf/encyclopedia-of-medicine-vol-1-5-3rd-edition_organized_organized.pdf")
    private Resource resource;
    private VectorStore vectorStore;

    public DocumentService(VectorStore vectorStore) {
        this.vectorStore = vectorStore;
    }

    public String createEmbeding() {
        PagePdfDocumentReader reader = new PagePdfDocumentReader(resource, PdfDocumentReaderConfig.builder().withPagesPerDocument(1).build());

        List<Document> documents = reader.read();
        List<Document> cleanedDocuments = new ArrayList<>();
        for (Document document : documents) {
            String text = document.getText();
            if (text == null || text.trim().length() <= 50) {
                continue;
            }
            String cleanedText = cleanText(text);
            Document cleanedDocument = new Document(cleanedText, document.getMetadata());
            cleanedDocuments.add(cleanedDocument);
        }
        System.out.println("Printing first 15 pages:");

        TokenTextSplitter splitter = TokenTextSplitter.builder().withChunkSize(500).withMinChunkSizeChars(50).build();
        List<Document> chunkedDocuments = splitter.apply(cleanedDocuments);
        System.out.println("Original pages: " + cleanedDocuments.size());
        System.out.println("Chunks created: " + chunkedDocuments.size());
        vectorStore.accept(chunkedDocuments);
        System.out.println("added into vector store");
        return "Added Successfully";

    }

    private String cleanText(String text) {
        return text.replace("â€˜", "'").replace("â€™", "'").replace("â€œ", "\"").replace("â€", "\"").replaceAll("\\s+", " ").trim();
    }
}


