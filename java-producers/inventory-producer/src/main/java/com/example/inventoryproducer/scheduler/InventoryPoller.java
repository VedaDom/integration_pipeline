package com.example.inventoryproducer.scheduler;

import com.example.inventoryproducer.model.Product;
import com.example.inventoryproducer.service.InventoryClient;
import com.example.inventoryproducer.service.KafkaPublisher;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import reactor.core.publisher.Flux;

@Component
public class InventoryPoller {
    private static final Logger log = LoggerFactory.getLogger(InventoryPoller.class);

    private final InventoryClient inventoryClient;
    private final KafkaPublisher publisher;

    public InventoryPoller(InventoryClient inventoryClient, KafkaPublisher publisher) {
        this.inventoryClient = inventoryClient;
        this.publisher = publisher;
    }

    // Poll every 15s by default
    @Scheduled(fixedDelayString = "${app.inventoryPollDelayMs:15000}")
    public void pollAndPublish() {
        log.info("Polling Inventory /products ...");
        Flux<Product> stream = inventoryClient.fetchProducts();
        stream.doOnNext(p -> publisher.send(p.getProduct_id(), p))
              .doOnComplete(() -> log.info("Inventory poll complete"))
              .doOnError(err -> log.error("Inventory poll failed", err))
              .subscribe();
    }
}
