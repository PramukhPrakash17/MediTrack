package com.pramukh.meditrack.Service;


import com.google.genai.Client;
import com.google.genai.types.GenerateContentResponse;
import com.pramukh.meditrack.Models.LabModels.DateWiseReports;
import com.pramukh.meditrack.Models.LabModels.LabReport;
import com.pramukh.meditrack.Models.MedicineModel.DateWiseMedicine;
import com.pramukh.meditrack.Models.MedicineModel.Medicine;
import com.pramukh.meditrack.Models.NotesModels.DateWiseNotes;

import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.util.List;

@Service
@RequiredArgsConstructor
public class SummaryService {
    private Client client;
    private LabReportService labReportService;
    private MedicineService medicineService;
    private NotesService notesService;

    @Autowired
    public SummaryService(Client client, LabReportService labReportService, MedicineService medicineService, NotesService notesService) {
        this.client = client;
        this.labReportService = labReportService;
        this.medicineService = medicineService;
        this.notesService = notesService;
    }

    public String getSummary(String InsuranceNumber) {
        String medicineInput = formatMedication(medicineService.getLastMedicines(InsuranceNumber));
        String labReportInput = formatLabReports(labReportService.getLatestLabReports(InsuranceNumber));
        String doctorNotesinput = formatDoctorNotes(notesService.getLatestNotes(InsuranceNumber));

        System.out.println("Medicine Input: " + medicineInput);
        System.out.println("Lab Report Input: " + labReportInput);
        System.out.println("Doctor Notes Input: " + doctorNotesinput);


        String prompt = "You are a medical assistant who gives summary" +
                "Doctor Notes:\n" + doctorNotesinput + "\n" +
                "Recent Medications:\n" + medicineInput + "\n" +
                "Lab Reports:\n" + labReportInput + "\n" + "If there is no data available  then say that no data available.\n"+ "If there any missing values in lab reports dont indicate that and concentrate on what disease or injury patient has and medication and notes provided with some lab report details" + "Summarize the above data in 3 lines.";

        System.out.println("Prompt: " + prompt);

        GenerateContentResponse response =
                client.models.generateContent(
                        "gemini-1.5-pro",
                        prompt,
                        null);

        System.out.println( "Response: " + response.text());
        return  response.text();
    }

    public String formatLabReports(DateWiseReports report) {
        if (report == null) {
            return "No lab reports available.";
        }
        StringBuilder sb = new StringBuilder();
        LocalDate uploadDate = report.getUploadDate();
        sb.append("Upload Date: ").append(uploadDate).append("\n");
        List<LabReport> reportDetails = report.getLabReports();
        for (LabReport labReport : reportDetails) {
            sb.append("Test Name: ").append(labReport.getTestName()).append("\n");
            sb.append("Value: ").append(labReport.getValue()).append("\n");
            sb.append("Unit: ").append(labReport.getUnit()).append("\n");
            sb.append("Reference Range: ").append(labReport.getReferenceRange()).append("\n");
            sb.append("-----------------------------\n");
        }
        return sb.toString();
    }

    public String formatMedication(DateWiseMedicine medicine) {
        if (medicine == null) {
            return "No medication available.";
        }
        StringBuilder sb = new StringBuilder();
        LocalDate date = medicine.getDate();
        sb.append("Date: ").append(date).append("\n");
        List<Medicine> medsList = medicine.getMedicines();
        for (Medicine med : medsList) {
            sb.append("Name: ").append(med.getName()).append("\n");
            sb.append("Dosage: ").append(med.getDosage()).append("\n");
            sb.append("Frequency: ").append(med.getFrequency()).append("\n");
            sb.append("Start Date: ").append(med.getStartDate()).append("\n");
            sb.append("End Date: ").append(med.getEndDate()).append("\n");
            sb.append("-----------------------------\n");
        }
        return sb.toString();
    }

    public String formatDoctorNotes(DateWiseNotes notes) {
        if (notes == null) {
            return "No doctor notes available.";
        }
        StringBuilder sb = new StringBuilder();
        LocalDate date = notes.getDate();
        sb.append("Date: ").append(date).append("\n");
        List<String> doctorNotes = notes.getDoctornotes();
        for (String note : doctorNotes) {
            sb.append("Note: ").append(note).append("\n");
            sb.append("-----------------------------\n");
        }
        return sb.toString();
    }
}
