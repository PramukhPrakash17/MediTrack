package com.pramukh.practice.rag.Controller;

import com.pramukh.practice.rag.Service.DocumentService;
import com.pramukh.practice.rag.Service.RagService;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("symptoms")
public class RagController {

    private DocumentService documentService;
    private RagService ragService;

    public RagController(DocumentService documentService, RagService ragService) {
        this.documentService = documentService;
        this.ragService = ragService;
    }

    @PostMapping("/createEmbedding")
    public String createEmbeddings() {
        return documentService.createEmbeding();
    }

    @GetMapping("/ask")
    public String askQuestion(@RequestBody String question) {
        return ragService.getAnswer(question);
    }


}
