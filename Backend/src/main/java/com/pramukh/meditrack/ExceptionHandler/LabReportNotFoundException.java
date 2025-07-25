package com.pramukh.meditrack.ExceptionHandler;

public class LabReportNotFoundException extends RuntimeException {
   public LabReportNotFoundException(String message) {
        super(message);
    }
}
