package com.pramukh.meditrack.Repository;

import com.pramukh.meditrack.Models.MedicalData;
import com.pramukh.meditrack.Models.Medicine;
import org.springframework.data.mongodb.repository.MongoRepository;

public interface MedicineRepository extends MongoRepository<MedicalData, String> {


}
