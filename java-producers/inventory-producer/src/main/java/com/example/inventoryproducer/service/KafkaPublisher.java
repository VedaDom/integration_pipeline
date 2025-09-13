package com.example.inventoryproducer.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.kafka.clients.producer.ProducerRecord;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;

@Service
public class KafkaPublisher {
    private static final Logger log = LoggerFactory.getLogger(KafkaPublisher.class);

    private final KafkaTemplate<String, String> kafkaTemplate;
    private final ObjectMapper objectMapper;
    private final String topic;
    private final String dlqTopic;

    public KafkaPublisher(KafkaTemplate<String, String> kafkaTemplate,
                          ObjectMapper objectMapper,
                          @Value("${app.inventoryTopic}") String topic,
                          @Value("${app.inventoryDlqTopic}") String dlqTopic) {
        this.kafkaTemplate = kafkaTemplate;
        this.objectMapper = objectMapper;
        this.topic = topic;
        this.dlqTopic = dlqTopic;
    }

    public void send(String key, Object payload) {
        try {
            String value = objectMapper.writeValueAsString(payload);
            ProducerRecord<String, String> record = new ProducerRecord<>(topic, key, value);
            doSend(record).whenComplete((result, ex) -> {
                if (ex != null) {
                    log.error("Failed to send to topic={} key={}: {}", topic, key, ex.toString());
                    sendToDlq(key, payload, ex);
                } else {
                    log.info("Sent record to topic={} partition={} offset={} key={} valueSize={}B",
                            result.getRecordMetadata().topic(),
                            result.getRecordMetadata().partition(),
                            result.getRecordMetadata().offset(),
                            key,
                            value.length());
                }
            });
        } catch (JsonProcessingException e) {
            log.error("JSON serialization error for key={}", key, e);
            sendToDlq(key, payload, e);
        }
    }

    protected java.util.concurrent.CompletableFuture<org.springframework.kafka.support.SendResult<String, String>> doSend(ProducerRecord<String, String> record) {
        return kafkaTemplate.send(record);
    }

    private void sendToDlq(String key, Object originalPayload, Throwable error) {
        try {
            String errorEnvelope = objectMapper.writeValueAsString(new DlqMessage(originalPayload, error.toString()));
            ProducerRecord<String, String> dlqRecord = new ProducerRecord<>(dlqTopic, key, errorEnvelope);
            doSend(dlqRecord).whenComplete((res, ex2) -> {
                if (ex2 != null) {
                    log.error("Failed to send to DLQ topic={} key={}: {}", dlqTopic, key, ex2.toString());
                } else {
                    log.warn("Sent record to DLQ topic={} key={} due to error: {}", dlqTopic, key, error.toString());
                }
            });
        } catch (Exception ex) {
            log.error("DLQ serialization/send failed for key={} after original error {}", key, error.toString(), ex);
        }
    }

    static class DlqMessage {
        public Object original;
        public String error;
        public DlqMessage(Object original, String error) {
            this.original = original;
            this.error = error;
        }
    }
}
