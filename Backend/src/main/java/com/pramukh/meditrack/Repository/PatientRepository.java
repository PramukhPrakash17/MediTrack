package com.pramukh.meditrack.Repository;

import com.pramukh.meditrack.Models.PatientDetails;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface PatientRepository extends JpaRepository<PatientDetails, Integer> {

    PatientDetails findByInsuranceNumber(String insuranceNumber);
}
