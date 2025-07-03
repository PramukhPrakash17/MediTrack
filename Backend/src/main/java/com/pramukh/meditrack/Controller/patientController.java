package com.pramukh.meditrack.Controller;

import com.pramukh.meditrack.DTO.PatientDetailsDto;
import com.pramukh.meditrack.DTO.PatientResponseDto;
import com.pramukh.meditrack.Service.PatientService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/patient")
public class patientController {

    private PatientService patientService;

    @Autowired
    public patientController(PatientService patientService) {
        this.patientService = patientService;
    }

    @PostMapping("/add")
    public ResponseEntity<String> addPatient(@RequestBody PatientDetailsDto patientDetailsDto) {
        patientService.addPatient(patientDetailsDto);
        return new ResponseEntity<>("Patient added successfully", HttpStatus.OK);
    }

    @GetMapping("/get/{insuranceNumber}")
    public ResponseEntity<PatientResponseDto> getPatientByInsuranceNumber(@PathVariable String insuranceNumber) {
        PatientResponseDto patient = patientService.getPatientByInsuranceNumber(insuranceNumber);
        return new ResponseEntity<>(patient, HttpStatus.OK);

    }
}
