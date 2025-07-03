package com.pramukh.meditrack.Service;

import com.pramukh.meditrack.DTO.PatientDetailsDto;
import com.pramukh.meditrack.DTO.PatientResponseDto;
import com.pramukh.meditrack.ExceptionHandler.PatientNotFoundException;
import com.pramukh.meditrack.Models.PatientDetails;
import com.pramukh.meditrack.Repository.PatientRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class PatientService {

    private final PatientRepository patientRepository;

    @Autowired
    public PatientService(PatientRepository patientRepository) {
        this.patientRepository = patientRepository;
    }

    public String addPatient(PatientDetailsDto patientDetailsDto) {
        PatientDetails patientDetails = new PatientDetails();
        patientDetails.setFirstName(patientDetailsDto.getFirstName());
        patientDetails.setLastName(patientDetailsDto.getLastName());
        patientDetails.setDateOfBirth(patientDetailsDto.getDateOfBirth());
        patientDetails.setInsuranceNumber(patientDetailsDto.getInsuranceNumber());
        patientDetails.setAddress(patientDetailsDto.getAddress());
        patientDetails.setPhoneNumber(patientDetailsDto.getPhoneNumber());
        patientDetails.setEmail(patientDetailsDto.getEmail());
        patientRepository.save(patientDetails);
        return "Patient added successfully";
    }

    public PatientResponseDto getPatientByInsuranceNumber(String insuranceNumber) {
        PatientDetails patientDetails = patientRepository.findByInsuranceNumber(insuranceNumber);
        if (patientDetails != null) {
            return new PatientResponseDto(patientDetails.getFirstName(), patientDetails.getLastName(), patientDetails.getDateOfBirth(), patientDetails.getAddress(), patientDetails.getPhoneNumber());
        }
        else {
            throw new PatientNotFoundException("No patient found with insurance number: " + insuranceNumber);
        }
    }
}
