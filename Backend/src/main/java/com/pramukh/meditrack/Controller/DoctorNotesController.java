package com.pramukh.meditrack.Controller;

import com.pramukh.meditrack.DTO.NotesRequestDto;
import com.pramukh.meditrack.Service.NotesService;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/doctornotes")
@CrossOrigin(origins = "*", methods = {RequestMethod.GET, RequestMethod.POST, RequestMethod.PUT, RequestMethod.DELETE, RequestMethod.OPTIONS}, allowedHeaders = {"Authorization", "Content-Type", "Accept"})
@Tag(name = "Notes API's")
public class DoctorNotesController {

    private NotesService notesService;

    @Autowired
    public DoctorNotesController(NotesService notesService) {
        this.notesService = notesService;
    }
    
    @PostMapping("/uploadnotes/{insuranceNumber}")
    public ResponseEntity<?> uploadnotes(@RequestBody NotesRequestDto notesRequestDto, @PathVariable String insuranceNumber) {
        return new ResponseEntity<>(notesService.saveNotes(notesRequestDto, insuranceNumber), HttpStatus.OK );
    }

    @GetMapping("/getnotes/{insuranceNumber}")
    public ResponseEntity<?> getNotes(@PathVariable String insuranceNumber) {
        return new ResponseEntity<>(notesService.getNotes(insuranceNumber), HttpStatus.OK);
    }
    @GetMapping("/getlatestnotes/{insuranceNumber}")
    public ResponseEntity<?> getLatestNotes(@PathVariable String insuranceNumber) {
        return new ResponseEntity<>(notesService.getLatestNotes(insuranceNumber), HttpStatus.OK);
    }
}
