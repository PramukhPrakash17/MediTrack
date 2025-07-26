package com.pramukh.meditrack.Repository;

import com.pramukh.meditrack.Models.MedicineModel.MedicalData;
import org.springframework.data.mongodb.repository.MongoRepository;

public interface MedicineRepository extends MongoRepository<MedicalData, String> {


}
