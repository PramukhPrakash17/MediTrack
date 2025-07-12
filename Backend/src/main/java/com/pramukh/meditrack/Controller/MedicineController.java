package com.pramukh.meditrack.Controller;

import com.pramukh.meditrack.Models.Medicine;
import com.pramukh.meditrack.Service.MedicineService;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/medicine")
@Tag(name = "Medicine API's")
public class MedicineController {

    private final MedicineService medicineService;

    @Autowired
    public MedicineController(MedicineService medicineService) {
        this.medicineService = medicineService;
    }

    @PostMapping("/addMedicine/{insuranceNumber}")
    public ResponseEntity<String> addMedicine(@PathVariable String insuranceNumber, @RequestBody List<Medicine> medicines) {
        String result = medicineService.addMedicine(insuranceNumber, medicines);
        return new ResponseEntity<>(result, HttpStatus.OK);
    }

    @GetMapping("/getMedicines/{insuranceNumber}")
    public ResponseEntity<List<Medicine>> getMedicines(@PathVariable String insuranceNumber) {
        List<Medicine> medicines = medicineService.getMedicines(insuranceNumber);
        return new ResponseEntity<>(medicines, HttpStatus.OK);
    }

    @GetMapping("/getLast5Medicines/{insuranceNumber}")
    public ResponseEntity<List<Medicine>> getLastFiveMedcines(@PathVariable String insuranceNumber , @RequestParam(defaultValue = "5") int limit) {
        List<Medicine> medicines = medicineService.getLastFiveMedicines(insuranceNumber, limit);
        return new ResponseEntity<>(medicines, HttpStatus.OK);
    }
}
