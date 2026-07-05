package com.pramukh.practice.drugragservice;

import com.pramukh.practice.drugragservice.service.DrugRagService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

@SpringBootTest
class DrugRagServiceAnxitTest {

    @Autowired
    private DrugRagService drugRagService;

    @Test
    void anxitQuestionReturnsGroundedAnswer() {
        String question = "What is anxit used for?";

        String answer = drugRagService.getAnswers(question);

        System.out.println("=== ANSWER ===");
        System.out.println(answer);
        System.out.println("==============");

        assertNotNull(answer);
        assertFalse(
                answer.toLowerCase().contains("was not found in the available drug dataset"),
                "Drug resolution should succeed for 'anxit'"
        );
        assertFalse(
                answer.toLowerCase().contains("this information is not available in the dataset"),
                "Vector retrieval should have found the anxit drug_knowledge document"
        );
        assertTrue(
                answer.toLowerCase().contains("anxiety") || answer.toLowerCase().contains("panic"),
                "Answer should mention anxit's known uses (anxiety/panic disorder) from the retrieved context"
        );
    }
}
