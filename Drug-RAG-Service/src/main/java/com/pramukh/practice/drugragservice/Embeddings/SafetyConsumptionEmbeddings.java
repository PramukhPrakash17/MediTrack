package com.pramukh.practice.drugragservice.Embeddings;

import com.opencsv.CSVReader;
import com.opencsv.exceptions.CsvValidationException;
import org.springframework.ai.document.Document;
import org.springframework.ai.vectorstore.VectorStore;
import org.springframework.core.io.ClassPathResource;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
public class SafetyConsumptionEmbeddings {

    private static final int BATCH_SIZE = 100;
    private static final long SLEEP_AFTER_EACH_BATCH_MS = 3000;
    private static final int MAX_RETRIES = 5;
    private static final Integer LIMIT = null;

    private static final String CSV_FILE = "Datasets/Safety+Consumption-Final.csv";
    private static final String DOCUMENT_TYPE = "patient_support";

    // Set true ONLY if you need to wipe and redo safety data.
    // This deletes ONLY patient_support rows — drug rows are never touched.
    private static final boolean FORCE_RESTART = false;

    private final VectorStore vectorStore;
    private final JdbcTemplate jdbcTemplate;

    public SafetyConsumptionEmbeddings(VectorStore vectorStore, JdbcTemplate jdbcTemplate) {
        this.vectorStore = vectorStore;
        this.jdbcTemplate = jdbcTemplate;
    }

    public void createEmbeddings() throws IOException, CsvValidationException, InterruptedException {

        ClassPathResource resource = new ClassPathResource(CSV_FILE);

        if (FORCE_RESTART) {
            int deleted = jdbcTemplate.update(
                    "DELETE FROM drug_vector_store WHERE metadata->>'documentType' = ?", DOCUMENT_TYPE);
            System.out.println("FORCE_RESTART: Deleted " + deleted + " existing safety/consumption rows. Drug rows untouched.");
        }

        int totalRows = countRows(resource);
        int existingRows = getExistingRowCount();

        if (LIMIT != null && LIMIT < totalRows) {
            totalRows = LIMIT;
        }

        System.out.println("================================================");
        System.out.println("SAFETY & CONSUMPTION EMBEDDING INGESTION STARTED");
        System.out.println("Batch size: " + BATCH_SIZE);
        System.out.println("Sleep after each batch: " + SLEEP_AFTER_EACH_BATCH_MS + " ms");
        System.out.println("Total rows in CSV: " + totalRows);
        System.out.println("Already in DB: " + existingRows + " — skipping");
        System.out.println("Rows to process: " + (totalRows - existingRows));
        System.out.println("================================================");

        if (existingRows >= totalRows) {
            System.out.println("All Safety & Consumption rows already embedded. Nothing to do.");
            return;
        }

        try (CSVReader csvReader = new CSVReader(new InputStreamReader(resource.getInputStream()))) {

            csvReader.readNext();

            for (int i = 0; i < existingRows; i++) {
                csvReader.readNext();
            }

            System.out.println("Skipped " + existingRows + " rows. Resuming from row " + (existingRows + 1));

            String[] record;
            List<Document> batch = new ArrayList<>();

            int totalProcessed = existingRows;
            int geminiRequests = 0;
            long startTime = System.currentTimeMillis();

            while ((record = csvReader.readNext()) != null) {

                if (LIMIT != null && totalProcessed >= LIMIT) {
                    break;
                }

                batch.add(buildDocument(record));

                if (batch.size() == BATCH_SIZE) {
                    acceptWithRetry(batch);
                    geminiRequests++;
                    totalProcessed += batch.size();
                    batch.clear();
                    printProgress(totalProcessed, totalRows, geminiRequests, startTime);
                    Thread.sleep(SLEEP_AFTER_EACH_BATCH_MS);
                }
            }

            if (!batch.isEmpty()) {
                acceptWithRetry(batch);
                geminiRequests++;
                totalProcessed += batch.size();
                printProgress(totalProcessed, totalRows, geminiRequests, startTime);
            }

            long elapsed = System.currentTimeMillis() - startTime;
            System.out.println("================================================");
            System.out.printf("DONE! %d rows embedded | %d Gemini API calls | Total time: %s%n",
                    totalProcessed, geminiRequests, formatDuration(elapsed));
            System.out.println("================================================");
        }
    }

    private void acceptWithRetry(List<Document> batch) throws InterruptedException {
        int attempt = 0;

        while (true) {
            try {
                long batchStart = System.currentTimeMillis();
                vectorStore.accept(batch);
                long batchTime = System.currentTimeMillis() - batchStart;
                System.out.println("Batch inserted successfully. Batch size: "
                        + batch.size() + " | Time: " + formatDuration(batchTime));
                return;

            } catch (Exception e) {
                attempt++;
                String errorMessage = e.getMessage() == null ? "" : e.getMessage();

                boolean retryable =
                        errorMessage.contains("429")
                                || errorMessage.toLowerCase().contains("resource exhausted")
                                || errorMessage.toLowerCase().contains("timeout")
                                || errorMessage.toLowerCase().contains("temporarily unavailable")
                                || errorMessage.toLowerCase().contains("503");

                if (!retryable || attempt > MAX_RETRIES) {
                    System.out.println("Batch failed permanently after " + attempt + " attempts.");
                    throw e;
                }

                long waitMs = calculateBackoff(attempt);
                System.out.println("Retryable error detected.");
                System.out.println("Attempt: " + attempt + "/" + MAX_RETRIES);
                System.out.println("Error: " + errorMessage);
                System.out.println("Waiting before retry: " + formatDuration(waitMs));
                Thread.sleep(waitMs);
            }
        }
    }

    private long calculateBackoff(int attempt) {
        return switch (attempt) {
            case 1 -> 10_000L;
            case 2 -> 20_000L;
            case 3 -> 40_000L;
            case 4 -> 60_000L;
            default -> 120_000L;
        };
    }

    private int getExistingRowCount() {
        try {
            Integer count = jdbcTemplate.queryForObject(
                    "SELECT COUNT(*) FROM drug_vector_store WHERE metadata->>'documentType' = ?",
                    Integer.class, DOCUMENT_TYPE);
            return count != null ? count : 0;
        } catch (Exception e) {
            System.out.println("Could not read existing row count — starting from 0. Reason: " + e.getMessage());
            return 0;
        }
    }

    private int countRows(ClassPathResource resource) throws IOException, CsvValidationException {
        int totalRows = 0;
        try (CSVReader counter = new CSVReader(new InputStreamReader(resource.getInputStream()))) {
            counter.readNext();
            while (counter.readNext() != null) totalRows++;
        }
        return totalRows;
    }

    private void printProgress(int processed, int total, int geminiRequests, long startTime) {
        long elapsed = System.currentTimeMillis() - startTime;
        int remaining = total - processed;
        double percent = (processed * 100.0) / total;

        long etaMs = 0;
        if (processed > 0 && elapsed > 0) {
            double rowsPerMs = (double) processed / elapsed;
            etaMs = (long) (remaining / rowsPerMs);
        }

        System.out.printf(
                "[%d/%d rows | %.2f%%] | Remaining: %d | Gemini calls: %d | Elapsed: %s | ETA: %s%n",
                processed, total, percent, remaining, geminiRequests,
                formatDuration(elapsed), formatDuration(etaMs));
    }

    private String formatDuration(long ms) {
        long totalSeconds = ms / 1000;
        long hours = totalSeconds / 3600;
        long minutes = (totalSeconds % 3600) / 60;
        long seconds = totalSeconds % 60;

        if (hours > 0) return String.format("%dh %dm %ds", hours, minutes, seconds);
        if (minutes > 0) return String.format("%dm %ds", minutes, seconds);
        return String.format("%ds", seconds);
    }

    private Document buildDocument(String[] record) {
        String text =
                "Drug name: " + value(record, 0) + ".\n" +
                "Age group: " + value(record, 2) + ".\n" +
                "Gender: " + value(record, 3) + ".\n" +
                "Consumption: " + value(record, 4) + ".\n" +
                "Pregnancy safety: " + value(record, 5) + ".\n" +
                "Alcohol interaction: " + value(record, 6) + ".\n" +
                "Prescription type: " + value(record, 7) + ".";

        Map<String, Object> metadata = new HashMap<>();
        metadata.put("drugName", value(record, 0));
        metadata.put("normalizedDrugName", value(record, 1));
        metadata.put("documentType", value(record, 8));

        return new Document(text, metadata);
    }

    private String value(String[] record, int index) {
        if (index >= record.length || record[index] == null || record[index].isBlank()) {
            return "Not available";
        }
        return record[index].trim();
    }
}
