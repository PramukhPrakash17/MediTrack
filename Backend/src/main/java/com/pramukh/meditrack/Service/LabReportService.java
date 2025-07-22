package com.pramukh.meditrack.Service;

import com.google.cloud.documentai.v1.Document;
import com.google.cloud.documentai.v1.DocumentProcessorServiceClient;
import com.google.cloud.documentai.v1.ProcessRequest;
import com.google.cloud.documentai.v1.RawDocument;
import com.google.protobuf.ByteString;
import com.pramukh.meditrack.Models.LabData;
import com.pramukh.meditrack.Models.LabReport;

import com.pramukh.meditrack.Repository.LabReportRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.time.Instant;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

@Service
public class LabReportService {

    private DocumentProcessorServiceClient client;
    private LabReportRepository labRepo;

    @Value("${gcp.project-id}")
    private String projectId;
    @Value("${gcp.document-ai.location}")
    private String location;
    @Value("${gcp.document-ai.processor-id}")
    private String processorId;


    @Autowired
    public LabReportService(DocumentProcessorServiceClient client, LabReportRepository labRepo) {
        this.client = client;
        this.labRepo = labRepo;
    }

    public String addLabReports(String insuranceNumber, MultipartFile file) throws IOException {

        String procName = String.format("projects/%s/locations/%s/processors/%s",
                projectId, location, processorId);
        Document doc = client.processDocument(
                ProcessRequest.newBuilder()
                        .setName(procName)
                        .setRawDocument(RawDocument.newBuilder()
                                .setContent(ByteString.copyFrom(file.getBytes()))
                                .setMimeType(file.getContentType()))
                        .build()
        ).getDocument();

        List<LabReport> newReports = new ArrayList<>();
        for (Document.Entity row : doc.getEntitiesList()) {
            if (!"lab_row".equals(row.getType())) {
                continue;
            }
            LabReport rpt = new LabReport();
            rpt.setUploadDate(Instant.now());
            for (Document.Entity cell : row.getPropertiesList()) {
                String text = extract(cell, doc);
                switch (cell.getType()) {
                    case "test_name" -> rpt.setTestName(text);
                    case "value" -> rpt.setValue(text);
                    case "unit" -> rpt.setUnit(text);
                    case "reference_range" -> rpt.setReferenceRange(text);
                }
            }
            newReports.add(rpt);
        }


        LabData data;
        Optional<LabData> existingData = labRepo.findById(insuranceNumber);
        if (existingData.isPresent()) {
            data = existingData.get();
        } else {
            data = new LabData();
            data.setInsuranceNumber(insuranceNumber);
        }

        List<LabReport> prevTests = data.getLabTests();
        prevTests.addAll(newReports);
        data.setLabTests(prevTests);
        labRepo.save(data);
        return "Lab reports added successfully";
    }

    private String extract(Document.Entity e, Document doc) {
        if (e == null) return "";
        StringBuilder sb = new StringBuilder();
        for (Document.TextAnchor.TextSegment seg : e.getTextAnchor().getTextSegmentsList()) {
            int s = (int) seg.getStartIndex(), t = (int) seg.getEndIndex();
            sb.append(doc.getText(), s, t);
        }
        return sb.toString().trim();
    }
}
