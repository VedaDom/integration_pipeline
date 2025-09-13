package com.example.crmproducer.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.kafka.clients.producer.ProducerRecord;
import org.junit.jupiter.api.Test;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CompletableFuture;

public class KafkaPublisherTest {

    @Test
    void send_success_publishes_to_main_topic() {
        ObjectMapper mapper = new ObjectMapper();
        List<String> topics = new ArrayList<>();
        KafkaPublisher publisher = new KafkaPublisher(null, mapper, "customer_data", "dlq_customer_data") {
            @Override
            protected java.util.concurrent.CompletableFuture<org.springframework.kafka.support.SendResult<String, String>> doSend(ProducerRecord<String, String> record) {
                topics.add(record.topic());
                return CompletableFuture.completedFuture(null);
            }
        };
        publisher.send("c1", new Payload("x"));
        assert topics.get(0).equals("customer_data");
    }

    @Test
    void send_failure_goes_to_dlq() {
        ObjectMapper mapper = new ObjectMapper();
        List<String> topics = new ArrayList<>();
        KafkaPublisher publisher = new KafkaPublisher(null, mapper, "customer_data", "dlq_customer_data") {
            boolean first = true;
            @Override
            protected java.util.concurrent.CompletableFuture<org.springframework.kafka.support.SendResult<String, String>> doSend(ProducerRecord<String, String> record) {
                topics.add(record.topic());
                if (first) {
                    first = false;
                    CompletableFuture<org.springframework.kafka.support.SendResult<String, String>> f = new CompletableFuture<>();
                    f.completeExceptionally(new RuntimeException("test"));
                    return f;
                }
                return CompletableFuture.completedFuture(null);
            }
        };
        publisher.send("c1", new Payload("x"));
        assert topics.size() >= 2 && topics.get(1).equals("dlq_customer_data");
    }

    static class Payload { public String v; Payload(String v){this.v=v;} }
}
