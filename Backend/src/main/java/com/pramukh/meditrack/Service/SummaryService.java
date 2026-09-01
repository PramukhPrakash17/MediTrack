package com.pramukh.meditrack.Service;


import com.pramukh.meditrack.DTO.LabReportSummaryEntry;
import com.pramukh.meditrack.DTO.MedicineSummaryEntry;
import com.pramukh.meditrack.DTO.NoteSummaryEntry;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

import java.time.LocalDate;
import java.util.List;
import java.util.Map;

@Service
public class SummaryService {
    private RestClient groqClient;
    private LabReportService labReportService;
    private MedicineService medicineService;
    private NotesService notesService;

    @Value("${groq.model}")
    private String groqModel;

    @Autowired
    public SummaryService(RestClient groqClient, LabReportService labReportService, MedicineService medicineService, NotesService notesService) {
        this.groqClient = groqClient;
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

        ChatResponse response = groqClient.post()
                .uri("/chat/completions")
                .body(Map.of(
                        "model", groqModel,
                        "messages", List.of(Map.of("role", "user", "content", prompt))
                ))
                .retrieve()
                .body(ChatResponse.class);

        String summary = response.choices().get(0).message().content();
        System.out.println("Response: " + summary);
        return summary;
    }

    private record ChatResponse(List<Choice> choices) {
        private record Choice(Message message) {}
        private record Message(String content) {}
    }

    public String formatLabReports(List<LabReportSummaryEntry> reports) {
        if (reports == null || reports.isEmpty()) {
            return "No lab reports available.";
        }
        StringBuilder sb = new StringBuilder();
        for (LabReportSummaryEntry report : reports) {
            sb.append("Upload Date: ").append(report.getRecordedDate()).append("\n");
            sb.append("Test Name: ").append(report.getTestName()).append("\n");
            sb.append("Value: ").append(report.getValue()).append("\n");
            sb.append("Unit: ").append(report.getUnit()).append("\n");
            sb.append("Reference Range: ").append(report.getReferenceRange()).append("\n");
            sb.append("-----------------------------\n");
        }
        return sb.toString();
    }

    public String formatMedication(List<MedicineSummaryEntry> medicines) {
        if (medicines == null || medicines.isEmpty()) {
            return "No medication available.";
        }
        StringBuilder sb = new StringBuilder();
        for (MedicineSummaryEntry med : medicines) {
            sb.append("Date: ").append(med.getRecordedDate()).append("\n");
            sb.append("Name: ").append(med.getName()).append("\n");
            sb.append("Dosage: ").append(med.getDosage()).append("\n");
            sb.append("Frequency: ").append(med.getFrequency()).append("\n");
            sb.append("Start Date: ").append(med.getStartDate()).append("\n");
            sb.append("End Date: ").append(med.getEndDate()).append("\n");
            sb.append("-----------------------------\n");
        }
        return sb.toString();
    }

    public String formatDoctorNotes(List<NoteSummaryEntry> notes) {
        if (notes == null || notes.isEmpty()) {
            return "No doctor notes available.";
        }
        StringBuilder sb = new StringBuilder();
        for (NoteSummaryEntry entry : notes) {
            sb.append("Date: ").append(entry.getRecordedDate()).append("\n");
            sb.append("Note: ").append(entry.getNote()).append("\n");
            sb.append("-----------------------------\n");
        }
        return sb.toString();
    }
}
