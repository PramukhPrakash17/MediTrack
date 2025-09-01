package com.pramukh.meditrack.Controller;

import com.pramukh.meditrack.DTO.MedicineDto;

import com.pramukh.meditrack.Models.MedicineModel.DateWiseMedicine;
import com.pramukh.meditrack.Models.MedicineModel.Medicine;
import com.pramukh.meditrack.Service.MedicineService;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/medicine")
@CrossOrigin(origins = "*", methods = {RequestMethod.GET, RequestMethod.POST, RequestMethod.PUT, RequestMethod.DELETE, RequestMethod.OPTIONS}, allowedHeaders = {"Authorization", "Content-Type", "Accept"})
@Tag(name = "Medicine API's")
public class MedicineController {

    private final MedicineService medicineService;

    @Autowired
    public MedicineController(MedicineService medicineService) {
        this.medicineService = medicineService;
    }

    @PostMapping("/addMedicine/{insuranceNumber}")
    public ResponseEntity<String> addMedicine(@PathVariable String insuranceNumber, @RequestBody List<MedicineDto> medicines) {
        String result = medicineService.addMedicine(insuranceNumber, medicines);
        return new ResponseEntity<>(result, HttpStatus.OK);
    }

    @GetMapping("/getMedicines/{insuranceNumber}")
    public ResponseEntity<List<DateWiseMedicine>> getMedicines(@PathVariable String insuranceNumber) {
        List<DateWiseMedicine> medicines = medicineService.getMedicines(insuranceNumber);
        return new ResponseEntity<>(medicines, HttpStatus.OK);
    }

    @GetMapping("/getLast5Medicines/{insuranceNumber}")
    public ResponseEntity<DateWiseMedicine> getLastFiveMedcines(@PathVariable String insuranceNumber) {
        DateWiseMedicine medicines = medicineService.getLastMedicines(insuranceNumber);
        return new ResponseEntity<>(medicines, HttpStatus.OK);
    }
}
