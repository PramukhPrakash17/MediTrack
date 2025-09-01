package com.pramukh.meditrack.Service;

import com.google.cloud.documentai.v1.Document;
import com.google.cloud.documentai.v1.DocumentProcessorServiceClient;
import com.google.cloud.documentai.v1.ProcessRequest;
import com.google.cloud.documentai.v1.RawDocument;
import com.google.protobuf.ByteString;
import com.pramukh.meditrack.Models.LabModels.DateWiseReports;
import com.pramukh.meditrack.Models.LabModels.LabData;
import com.pramukh.meditrack.Models.LabModels.LabReport;
import com.pramukh.meditrack.Repository.LabReportRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.time.LocalDate;
import java.time.ZoneId;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;


@Service
public class LabReportService {

    private final DocumentProcessorServiceClient client;
    private final LabReportRepository labRepo;

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
        System.out.println("Entered addLabReports method");
        String procName = String.format("projects/%s/locations/%s/processors/%s", projectId, location, processorId);

        Document doc = client.processDocument(ProcessRequest.newBuilder().setName(procName).setRawDocument(RawDocument.newBuilder().setContent(ByteString.copyFrom(file.getBytes())).setMimeType(file.getContentType())).build()).getDocument();

        List<LabReport> newReports = new ArrayList<>();
        for (Document.Entity row : doc.getEntitiesList()) {
            if (!"lab_row".equals(row.getType())) {
                continue;
            }
            LabReport rpt = new LabReport();
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

        LabData data = labRepo.findById(insuranceNumber).orElseGet(() -> {
            LabData ld = new LabData();
            ld.setInsuranceNumber(insuranceNumber);
            return ld;
        });

        System.out.println("Lab Report found for insurance number");

        LocalDate today = LocalDate.now(ZoneId.systemDefault());
        DateWiseReports todayBucket = null;
        for (DateWiseReports bucket : data.getDateWiseReports()) {
            if (bucket.getUploadDate() != null && bucket.getUploadDate().equals(today)) {
                todayBucket = bucket;
                break;
            }
        }

        System.out.println("Checking for existing date bucket");

        if (todayBucket == null) {
            todayBucket = new DateWiseReports();
            todayBucket.setUploadDate(today);
            data.getDateWiseReports().add(todayBucket);
        }

        System.out.println("Adding new lab reports to today's bucket");

        todayBucket.getLabReports().addAll(newReports);
        labRepo.save(data);
        System.out.println("Lab reports added successfully for insurance number: " + insuranceNumber);
        return "Lab reports added successfully";
    }

    private String extract(Document.Entity e, Document doc) {
        if (e == null) return "";
        StringBuilder sb = new StringBuilder();
        for (Document.TextAnchor.TextSegment seg : e.getTextAnchor().getTextSegmentsList()) {
            int s = (int) seg.getStartIndex();
            int t = (int) seg.getEndIndex();
            sb.append(doc.getText(), s, t);
        }
        return sb.toString().trim();
    }


    public List<DateWiseReports> getLabReport(String insuranceNumber) {
        LabData labData = labRepo.findById(insuranceNumber).orElse(null);
        if (labData == null || labData.getDateWiseReports() == null) {
            return Collections.emptyList();
        }
        return labData.getDateWiseReports();
    }

    public DateWiseReports getLatestLabReports(String insuranceNumber) {
        LabData labData = labRepo.findById(insuranceNumber).orElse(null);
        if (labData == null || labData.getDateWiseReports() == null) {
            return null;
        }
        List<DateWiseReports> dateWiseReports = labData.getDateWiseReports();
        DateWiseReports latestReport = dateWiseReports.get(dateWiseReports.size() - 1);

        return latestReport;
    }
}