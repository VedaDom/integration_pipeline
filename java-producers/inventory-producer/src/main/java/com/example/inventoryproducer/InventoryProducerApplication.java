package com.example.inventoryproducer;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableScheduling
public class InventoryProducerApplication {
    public static void main(String[] args) {
        SpringApplication.run(InventoryProducerApplication.class, args);
    }
}
