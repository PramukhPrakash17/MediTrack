package com.pramukh.meditrack.ExceptionHandler;

public class PatientNotFoundException extends RuntimeException{
    public PatientNotFoundException(String message) {
        super(message);
    }

}
