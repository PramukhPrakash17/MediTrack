package com.pramukh.meditrack.Models;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.Date;

@Data
@AllArgsConstructor
@NoArgsConstructor
@Entity
public class PatientDetails {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private int PatientId;

    private String FirstName;

    private String LastName;

    private Date DateOfBirth;

    @Column(unique=true)
    private String InsuranceNumber;

    private String Address;

    private String PhoneNumber;

    private String email;

}
