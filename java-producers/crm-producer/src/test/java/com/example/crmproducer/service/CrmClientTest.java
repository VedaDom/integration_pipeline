package com.example.crmproducer.service;

import com.example.crmproducer.model.Customer;
import okhttp3.mockwebserver.MockResponse;
import okhttp3.mockwebserver.MockWebServer;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.test.StepVerifier;

import java.io.IOException;

public class CrmClientTest {
    static MockWebServer server;

    @BeforeAll
    static void setup() throws IOException {
        server = new MockWebServer();
        server.start();
    }

    @AfterAll
    static void tearDown() throws IOException {
        server.shutdown();
    }

    @Test
    void fetchCustomers_returnsItems() {
        String body = """
            [
              {"id":"c1","email":"a@example.com","name":"Alice","status":"active"},
              {"id":"c2","email":"b@example.com","name":"Bob","status":"inactive"}
            ]
        """;
        server.enqueue(new MockResponse().setResponseCode(200).setBody(body).addHeader("Content-Type", "application/json"));

        WebClient webClient = WebClient.builder().baseUrl(server.url("/").toString()).build();
        CrmClient client = new CrmClient(webClient);

        StepVerifier.create(client.fetchCustomers())
            .expectNextMatches(c -> c instanceof Customer && ((Customer)c).getId().equals("c1"))
            .expectNextMatches(c -> c instanceof Customer && ((Customer)c).getId().equals("c2"))
            .verifyComplete();
    }
}
