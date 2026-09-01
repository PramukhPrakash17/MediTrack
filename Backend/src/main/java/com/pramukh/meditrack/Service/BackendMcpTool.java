package com.pramukh.meditrack.Service;

import com.pramukh.meditrack.DTO.MedicineDto;
import com.pramukh.meditrack.DTO.NotesRequestDto;
import org.springaicommunity.mcp.annotation.McpTool;
import org.springaicommunity.mcp.annotation.McpToolParam;
import org.springframework.stereotype.Component;

import java.util.List;

@Component
public class BackendMcpTool {

    private final MedicineService medicineService;
    private final NotesService notesService;

    public BackendMcpTool(MedicineService medicineService, NotesService notesService) {
        this.medicineService = medicineService;
        this.notesService = notesService;
    }

    @McpTool(name = "add_medicine", description = "Add one or more medicines to a patient's record in MediTrack.\n" +
            "\n" +
            "Use this tool whenever the doctor explicitly asks to add, prescribe, or record medication(s) for a patient. " +
            "Every medicine the doctor names in the same request should be included in a single call, not one call per medicine.\n" +
            "\n" +
            "For each medicine, provide its name, frequency formatted as morning-afternoon-night shorthand (e.g. 1-0-1, 0-0-1), " +
            "start date and end date resolved against today's actual date, and any instructions the doctor gave. Leave dosage " +
            "blank if the doctor did not state a dosage strength - never invent one.\n" +
            "\n" +
            "Do not use this tool to look up information about a drug (uses, side effects, dosage guidance) - use " +
            "drug_information for that instead.")
    public String addMedicine(
            @McpToolParam(description = "The patient's insurance number.", required = true) String insuranceNumber,
            @McpToolParam(description = "The medicine(s) to add.", required = true) List<MedicineDto> medicines) {
        return medicineService.addMedicine(insuranceNumber, medicines);
    }

    @McpTool(name = "add_doctor_note", description = "Add a free-text clinical note to a patient's record in MediTrack.\n" +
            "\n" +
            "Use this tool whenever the doctor explicitly asks to add, save, or record a note for a patient. Pass the note " +
            "text as the doctor described it.\n" +
            "\n" +
            "Do not use this tool for lab/blood reports or X-ray images - those are handled by their own tools.")
    public String addDoctorNote(
            @McpToolParam(description = "The patient's insurance number.", required = true) String insuranceNumber,
            @McpToolParam(description = "The note text to add.", required = true) String note) {
        NotesRequestDto dto = new NotesRequestDto();
        dto.setNotes(note);
        return notesService.saveNotes(dto, insuranceNumber);
    }
}
