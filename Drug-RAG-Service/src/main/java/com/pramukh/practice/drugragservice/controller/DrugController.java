package com.pramukh.practice.drugragservice.controller;

import com.opencsv.exceptions.CsvValidationException;
import com.pramukh.practice.drugragservice.service.DrugRagService;
import com.pramukh.practice.drugragservice.Embeddings.drugMappingService;
import org.springframework.web.bind.annotation.*;

import java.io.IOException;

@RestController
@RequestMapping("/drug")
public class DrugController {

    private drugMappingService drugMappingService;
    private DrugRagService ragService;

    public DrugController(drugMappingService drugMappingService, DrugRagService ragService) {
        this.drugMappingService = drugMappingService;
        this.ragService = ragService;
    }

    @PostMapping("/addMaping")
    public String mapping() throws CsvValidationException, IOException {
        return drugMappingService.creatingMapping();
    }

    @GetMapping ("/ask")
    public String answers(@RequestBody String question){
        System.out.println("[CONTROLLER] Step 0: Received question: " + question);
        String result = ragService.getAnswers(question);
        System.out.println("[CONTROLLER] Step 5: Sending response back to client");
        return result;
    }
}
