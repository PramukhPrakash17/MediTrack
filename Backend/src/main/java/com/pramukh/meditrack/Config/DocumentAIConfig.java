package com.pramukh.meditrack.Config;

import com.google.api.gax.core.CredentialsProvider;

import com.google.cloud.documentai.v1.DocumentProcessorServiceClient;
import com.google.cloud.documentai.v1.DocumentProcessorServiceSettings;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.io.FileInputStream;
import java.io.IOException;

@Configuration
public class DocumentAIConfig {
    @Value("${gcp.document-ai.location}")
    private String location;


    @Bean
    public DocumentProcessorServiceClient documentProcessorServiceClient(CredentialsProvider credentialsProvider) throws IOException {
        String endpoint = String.format("%s-documentai.googleapis.com:443", location);

        DocumentProcessorServiceSettings settings =
                DocumentProcessorServiceSettings.newBuilder()
                        .setEndpoint(endpoint)
                        .setCredentialsProvider(credentialsProvider)
                        .build();
        return DocumentProcessorServiceClient.create(settings);
    }
}

