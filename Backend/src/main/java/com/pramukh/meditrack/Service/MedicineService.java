package com.pramukh.meditrack.Service;

import com.pramukh.meditrack.DTO.MedicineDto;

import com.pramukh.meditrack.ExceptionHandler.MedicineNotFoundException;
import com.pramukh.meditrack.Models.MedicineModel.DateWiseMedicine;
import com.pramukh.meditrack.Models.MedicineModel.MedicalData;
import com.pramukh.meditrack.Models.MedicineModel.Medicine;
import com.pramukh.meditrack.Repository.MedicineRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.time.ZoneId;
import java.util.Collections;
import java.util.List;

import java.util.stream.Collectors;

@Service
public class MedicineService {


    private MedicineRepository medicineRepository;

    @Autowired
    public MedicineService(MedicineRepository medicineRepository) {
        this.medicineRepository = medicineRepository;
    }


    public String addMedicine(String insuranceNumber, List<MedicineDto> medicineDtoList) {
        MedicalData data = medicineRepository.findById(insuranceNumber).orElseGet(() -> {
            MedicalData newMedicalData = new MedicalData();
            newMedicalData.setInsuranceNumber(insuranceNumber);
            return newMedicalData;
        });

        System.out.println("Step2");
        LocalDate today = LocalDate.now(ZoneId.systemDefault());
        DateWiseMedicine todaysMedicine = null;
        for (DateWiseMedicine medicine : data.getDateWiseMedicines()) {
            if (medicine.getDate().equals(today)) {
                todaysMedicine = medicine;
                break;
            }
        }

        if (todaysMedicine == null) {
            todaysMedicine = new DateWiseMedicine();
            todaysMedicine.setDate(today);
            data.getDateWiseMedicines().add(todaysMedicine);
        }

        List<Medicine> medsList = medicineDtoList.stream().map((dto) -> {
            Medicine m = new Medicine();
            m.setName(dto.getName());
            m.setDosage(dto.getDosage());
            m.setFrequency(dto.getFrequency());
            m.setStartDate(dto.getStartDate());
            m.setEndDate(dto.getEndDate());
            m.setInstructions(dto.getInstructions());
            return m;
        }).collect(Collectors.toList());
        todaysMedicine.getMedicines().addAll(medsList);
        medicineRepository.save(data);
        return "Medicine added successfully";
    }

    public List<DateWiseMedicine> getMedicines(String insuranceNumber) {
        MedicalData medicalData = medicineRepository.findById(insuranceNumber).orElse(null);
        if(medicalData==null || medicalData.getDateWiseMedicines()==null)
        {
            return Collections.emptyList();
        }
        return medicalData.getDateWiseMedicines();
    }

    public DateWiseMedicine getLastMedicines(String insuranceNumber) {
        List<DateWiseMedicine> medicines = getMedicines(insuranceNumber);
        if(medicines.isEmpty())
        {
            return null;
        }
        return medicines.get(medicines.size() - 1);

    }
}




