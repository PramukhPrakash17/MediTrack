package com.pramukh.meditrack.Repository;

import com.pramukh.meditrack.Models.LabData;
import com.pramukh.meditrack.Models.LabReport;
import com.pramukh.meditrack.Models.MedicalData;
import org.springframework.data.mongodb.repository.MongoRepository;

public interface LabReportRepository extends MongoRepository<LabData, String> {
}
