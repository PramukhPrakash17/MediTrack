package com.pramukh.meditrack.DTO;

import com.pramukh.meditrack.Models.ENUM.Gender;
import com.pramukh.meditrack.Models.ENUM.Role;

import java.time.LocalDate;

public class SignUpDTO {
    public String firstName;
    public String lastName;
    public String email;
    public String password;
    public Role role;
    public Gender gender;
    public LocalDate dateOfBirth;
    public String phoneNumber;
    public String insuranceNumber;
    public String address;
}
