package com.pramukh.meditrack.ExceptionHandler;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ExceptionHandler;

@ControllerAdvice
public class GlobalExceptionHandler {
    @ExceptionHandler(PatientNotFoundException.class)
    public ResponseEntity<String> handlePatientNotFoundException(PatientNotFoundException e) {

        return new ResponseEntity<>("Patient not found: " + e.getMessage(), HttpStatus.NOT_FOUND);
    }

    @ExceptionHandler(MedicineNotFoundException.class)
    public ResponseEntity<String> handleMedicineNotFoundException(MedicineNotFoundException e) {

        return new ResponseEntity<>("Medicine not found: " + e.getMessage(), HttpStatus.NOT_FOUND);
    }
}
