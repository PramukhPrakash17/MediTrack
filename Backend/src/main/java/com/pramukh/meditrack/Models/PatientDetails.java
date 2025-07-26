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
    private int patientId;

    private String firstName;

    private String lastName;

    private Date dateOfBirth;

    @Column(unique=true)
    private String insuranceNumber;

    private String address;

    private String phoneNumber;

    private String email;

}
