package com.pramukh.meditrack.Service;

import com.pramukh.meditrack.Models.MedicalData;
import com.pramukh.meditrack.Models.Medicine;
import com.pramukh.meditrack.Repository.MedicineRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.List;
import java.util.Optional;

@Service
public class MedicineService {


    private MedicineRepository medicineRepository;

    @Autowired
    public MedicineService(MedicineRepository medicineRepository) {
        this.medicineRepository = medicineRepository;
    }


    public String addMedicine(String insuranceNumber, List<Medicine> medicines) {
        MedicalData data;
        for (Medicine medicine : medicines) {
            medicine.setPrescribedAt(Instant.now());
        }
        Optional<MedicalData> existingData = medicineRepository.findById(insuranceNumber);
        if (existingData.isPresent()) {
            data = existingData.get();
        } else {
            data = new MedicalData();
            data.setInsuranceNumber(insuranceNumber);
        }
        List<Medicine> prevMedicines = data.getMedicines();

        prevMedicines.addAll(medicines);
        data.setMedicines(prevMedicines);
        medicineRepository.save(data);

        return "Medicine added successfully";
    }

    public List<Medicine> getMedicines(String insuranceNumber) {
        Optional<MedicalData> medicalData = medicineRepository.findById(insuranceNumber);
        if (medicalData.isPresent()) {
            return medicalData.get().getMedicines();
        } else {
            throw new RuntimeException("No medical data found for insurance number: " + insuranceNumber);
        }
    }

    //Similarly ike the above getMedicines method, you can implement a method which return only the number of last 5 entries in the list
    public List<Medicine> getLastFiveMedicines(String insuranceNumber,int limit) {

        List<Medicine> medicines = getMedicines(insuranceNumber);
        int size = medicines.size();
        if (size <= limit) {
            return medicines;
        } else {
            return medicines.subList(size - limit, size);
        }
    }
}
