package com.pramukh.practice.drugragservice.service;

import com.pramukh.practice.drugragservice.DTO.DrugResolutionResult;
import com.pramukh.practice.drugragservice.entity.DrugMapping;
import com.pramukh.practice.drugragservice.repository.DrugRepository;
import org.springframework.stereotype.Service;
import java.util.List;

@Service
public class DrugResolveService {

    private DrugRepository drugRepository;

    public DrugResolveService(DrugRepository drugRepository) {
        this.drugRepository = drugRepository;
    }

    public DrugResolutionResult resolveDrug(String drugName) {
        System.out.println("[RESOLVE-SERVICE] Step 2.1: Trying exact match for drug: " + drugName);
        List<DrugMapping> exactMatch = drugRepository.findDrugNameMatch(drugName);
        if (!exactMatch.isEmpty()) {
            DrugMapping match = exactMatch.get(0);
            System.out.println("[RESOLVE-SERVICE] Step 2.1 Result: Exact match found");
            System.out.println("  - Matched Drug Name: " + match.getDrugName());
            System.out.println("  - Normalized Drug Name: " + match.getNormalizedDrugName());
            return new DrugResolutionResult(match.getNormalizedDrugName(), match.getDrugName(), true);
        }
        System.out.println("[RESOLVE-SERVICE] Step 2.1 Result: No exact match found");
        
        System.out.println("[RESOLVE-SERVICE] Step 2.2: Trying normalized match for drug: " + drugName);
        List<DrugMapping> normalizedDrugMatch = drugRepository.findNormalizedDrugMatch(drugName);
        if (!normalizedDrugMatch.isEmpty()) {
            DrugMapping match = normalizedDrugMatch.get(0);
            System.out.println("[RESOLVE-SERVICE] Step 2.2 Result: Normalized match found");
            System.out.println("  - Normalized Drug Name: " + match.getNormalizedDrugName());
            return new DrugResolutionResult(match.getNormalizedDrugName(), null, false);
        }
        System.out.println("[RESOLVE-SERVICE] Step 2.2 Result: No normalized match found");

        if (!shouldAttemptFormulationCompletion(drugName)) {
            System.out.println("[RESOLVE-SERVICE] Step 2.3: Formulation completion not applicable, throwing error");
            throw new RuntimeException("Drug not found");
        }

        System.out.println("[RESOLVE-SERVICE] Step 2.3: Trying fallback match for drug: " + drugName);
        List<DrugMapping> fallbackMatches = drugRepository.findFallbackMatch(drugName);
        if (!fallbackMatches.isEmpty()) {
            DrugMapping match = fallbackMatches.get(0);
            System.out.println("[RESOLVE-SERVICE] Step 2.3 Result: Fallback match found");
            System.out.println("  - Matched Drug Name: " + match.getDrugName());
            System.out.println("  - Normalized Drug Name: " + match.getNormalizedDrugName());
            return new DrugResolutionResult(match.getNormalizedDrugName(), match.getDrugName(), true);
        }
        System.out.println("[RESOLVE-SERVICE] Step 2.3 Result: No fallback match found, throwing error");

        throw new RuntimeException("Unable to find drug : " + drugName);
    }

    private boolean shouldAttemptFormulationCompletion(String drugName) {

        if (drugName == null || drugName.isBlank()) {
            return false;
        }

        String cleaned = drugName.trim().toLowerCase();

        boolean hasNumber = cleaned.matches(".*\\d.*");

        boolean hasFormulationWord = cleaned.contains("tablet") || cleaned.contains("capsule") || cleaned.contains("syrup") || cleaned.contains("gel") || cleaned.contains("mg") || cleaned.contains("suspension") || cleaned.contains("injection");

        return hasNumber || hasFormulationWord;
    }


}
