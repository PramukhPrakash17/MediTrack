package com.pramukh.practice.drugragservice.Embeddings;

import com.opencsv.CSVReader;
import com.opencsv.exceptions.CsvValidationException;

import com.pramukh.practice.drugragservice.entity.DrugMapping;
import com.pramukh.practice.drugragservice.repository.DrugRepository;
import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.List;

@Service
public class drugMappingService {
    private final DrugRepository repository;

    public drugMappingService(DrugRepository repository) {
        this.repository = repository;
    }

    public String creatingMapping() throws CsvValidationException, IOException {
        String[] record;
        List<DrugMapping> mappings = new ArrayList<>();
        ClassPathResource resource = new ClassPathResource("Datasets/Medicine-Dataset-Final-Cleaned.csv");

        try (CSVReader reader = new CSVReader(new InputStreamReader(resource.getInputStream()))) {
            reader.readNext();
            while ((record = reader.readNext()) != null) {
                DrugMapping drugMappingobj = new DrugMapping(record[0], record[1]);
                mappings.add(drugMappingobj);
            }
            repository.saveAll(mappings);
        }
        return "Mapping created";
    }
}
