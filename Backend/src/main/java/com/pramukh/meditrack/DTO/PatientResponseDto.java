package com.pramukh.meditrack.DTO;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.Date;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class PatientResponseDto {
    private String firstName;
    private String lastName;
    private Date dateOfBirth;
    private String address;
    private String phoneNumber;

}
