package com.pramukh.meditrack.Controller;

import com.pramukh.meditrack.Service.SummaryService;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;


@RestController
@RequestMapping("/api/summary")
@CrossOrigin(origins = "*", methods = {RequestMethod.GET, RequestMethod.POST, RequestMethod.PUT, RequestMethod.DELETE, RequestMethod.OPTIONS}, allowedHeaders = {"Authorization", "Content-Type", "Accept"})
@Tag(name = "Summary API")
public class SummaryController {

    private SummaryService summaryService;

    @Autowired
    public SummaryController(SummaryService summaryService) {
        this.summaryService = summaryService;
    }

    @GetMapping("/getSummary/{insuranceNumber}")
    public ResponseEntity<String> getSummary(@PathVariable String insuranceNumber) {
        String summary = summaryService.getSummary(insuranceNumber);
        return new ResponseEntity<>(summary, HttpStatus.OK);
    }
}
