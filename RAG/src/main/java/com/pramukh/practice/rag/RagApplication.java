package com.pramukh.practice.rag;

import com.pramukh.practice.rag.Service.DocumentService;
import com.pramukh.practice.rag.Service.RagService;
import org.springframework.ai.support.ToolCallbacks;
import org.springframework.ai.tool.ToolCallback;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;

import java.util.List;

@SpringBootApplication
public class RagApplication {

    public static void main(String[] args) {
        SpringApplication.run(RagApplication.class, args);
        System.out.println("Hare Krishna!");
    }


}
