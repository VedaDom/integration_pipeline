package com.example.crmproducer;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableScheduling
public class CrmProducerApplication {
    public static void main(String[] args) {
        SpringApplication.run(CrmProducerApplication.class, args);
    }
}
