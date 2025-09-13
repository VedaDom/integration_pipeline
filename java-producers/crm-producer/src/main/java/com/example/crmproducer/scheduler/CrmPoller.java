package com.example.crmproducer.scheduler;

import com.example.crmproducer.model.Customer;
import com.example.crmproducer.service.CrmClient;
import com.example.crmproducer.service.KafkaPublisher;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import reactor.core.publisher.Flux;

@Component
public class CrmPoller {
    private static final Logger log = LoggerFactory.getLogger(CrmPoller.class);

    private final CrmClient crmClient;
    private final KafkaPublisher publisher;

    public CrmPoller(CrmClient crmClient, KafkaPublisher publisher) {
        this.crmClient = crmClient;
        this.publisher = publisher;
    }

    // Poll every 15s by default
    @Scheduled(fixedDelayString = "${app.crmPollDelayMs:15000}")
    public void pollAndPublish() {
        log.info("Polling CRM /customers ...");
        Flux<Customer> stream = crmClient.fetchCustomers();
        stream.doOnNext(c -> publisher.send(c.getId(), c))
              .doOnComplete(() -> log.info("CRM poll complete"))
              .doOnError(err -> log.error("CRM poll failed", err))
              .subscribe();
    }
}
