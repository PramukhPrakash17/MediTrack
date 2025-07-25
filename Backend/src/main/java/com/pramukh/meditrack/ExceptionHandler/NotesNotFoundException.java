package com.pramukh.meditrack.ExceptionHandler;

public class NotesNotFoundException extends RuntimeException{
    public NotesNotFoundException(String message) {
        super(message);
    }
}
