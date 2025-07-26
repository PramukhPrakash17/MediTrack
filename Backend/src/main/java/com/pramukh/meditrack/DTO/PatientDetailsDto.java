package com.pramukh.meditrack.DTO;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.util.Date;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class PatientDetailsDto {
    private String firstName;
    private String lastName;
    private Date dateOfBirth;
    private String insuranceNumber;
    private String address;
    private String phoneNumber;
    private String email;
}
