package com.pramukh.meditrack.Repository;

import com.pramukh.meditrack.Models.LabModels.LabData;
import org.springframework.data.mongodb.repository.MongoRepository;

public interface LabReportRepository extends MongoRepository<LabData, String> {
}
