package com.pramukh.meditrack.Models.NotesModels;


import lombok.Data;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;


import java.util.ArrayList;
import java.util.List;

@Data
@Document(collection = "notes")
public class Notes {
    @Id
    private String insuranceNumber;
    private List<DateWiseNotes> dateWiseNotes = new ArrayList<>();
}
