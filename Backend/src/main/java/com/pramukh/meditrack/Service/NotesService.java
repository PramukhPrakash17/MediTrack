package com.pramukh.meditrack.Service;

import com.pramukh.meditrack.DTO.NoteSummaryEntry;
import com.pramukh.meditrack.DTO.NotesRequestDto;
import com.pramukh.meditrack.ExceptionHandler.NotesNotFoundException;
import com.pramukh.meditrack.Models.NotesModels.DateWiseNotes;
import com.pramukh.meditrack.Models.NotesModels.Notes;
import com.pramukh.meditrack.Repository.NotesRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.time.ZoneId;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

@Service
public class NotesService {
    private NotesRepository notesRepository;

    @Autowired
    public NotesService(NotesRepository notesRepository) {
        this.notesRepository = notesRepository;
    }

    public String saveNotes(NotesRequestDto requestDto, String insuranceNumber) {
        Notes data = notesRepository.findById(insuranceNumber).orElseGet(() -> {
            Notes newNotes = new Notes();
            newNotes.setInsuranceNumber(insuranceNumber);
            return newNotes;
        });
        LocalDate today = LocalDate.now(ZoneId.systemDefault());
        DateWiseNotes todaysNotes = null;
        for (DateWiseNotes note : data.getDateWiseNotes()) {
            if (note.getDate().equals(today)) {
                todaysNotes = note;
                break;
            }
        }

        if (todaysNotes == null) {
            todaysNotes = new DateWiseNotes();
            todaysNotes.setDate(today);
            data.getDateWiseNotes().add(todaysNotes);
        }

        todaysNotes.getDoctornotes().add(requestDto.getNotes());
        notesRepository.save(data);
        return "Notes saved successfully";

    }

    public List<DateWiseNotes> getNotes(String insuranceNumber) {
        Notes notes = notesRepository.findById(insuranceNumber).orElse(null);
        if(notes==null || notes.getDateWiseNotes()==null)
        {
            return Collections.emptyList();
        }
        return notes.getDateWiseNotes();
    }

    /**
     * The last 5 notes across all dates, most recent first - see
     * MedicineService.getLastMedicines for why this flattens across dates
     * instead of returning only the newest date-bucket wholesale.
     */
    public List<NoteSummaryEntry> getLatestNotes(String insuranceNumber) {
        Notes notes = notesRepository.findById(insuranceNumber).orElse(null);
        List<NoteSummaryEntry> result = new ArrayList<>();
        if (notes == null || notes.getDateWiseNotes() == null) {
            return result;
        }
        List<DateWiseNotes> dateWiseNotes = notes.getDateWiseNotes();
        for (int i = dateWiseNotes.size() - 1; i >= 0 && result.size() < 5; i--) {
            DateWiseNotes bucket = dateWiseNotes.get(i);
            List<String> notesInBucket = bucket.getDoctornotes();
            for (int j = notesInBucket.size() - 1; j >= 0 && result.size() < 5; j--) {
                NoteSummaryEntry entry = new NoteSummaryEntry();
                entry.setNote(notesInBucket.get(j));
                entry.setRecordedDate(bucket.getDate());
                result.add(entry);
            }
        }
        return result;
    }

}
