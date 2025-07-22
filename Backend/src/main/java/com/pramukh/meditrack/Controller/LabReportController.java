package com.pramukh.meditrack.Controller;

import com.pramukh.meditrack.Service.LabReportService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartException;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;

@RestController
@RequestMapping("/api/labreport")
public class LabReportController {

    private LabReportService labReportService;

    @Autowired
    public LabReportController(LabReportService labReportService) {
        this.labReportService = labReportService;
    }

    @PostMapping(value ="/upload/{insuranceNumber}", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<String> uploadLabReport(@RequestParam("file") MultipartFile file, @PathVariable String insuranceNumber) throws IOException {
        System.out.println(file.getSize());
        System.out.println(file.getContentType());
        if (file.isEmpty() || file.getSize() == 0 || (!file.getContentType().equals("application/pdf") && !file.getContentType().equals("image/png") && !file.getContentType().equals("image/jpg"))) {
            throw new MultipartException("File validation failed: File is empty or not a valid format. Please upload a PDF, PNG, or JPG file.");
        }
        String response = labReportService.addLabReports(insuranceNumber, file);
        return ResponseEntity.ok(response);
    }
}
