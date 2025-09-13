package com.example.inventoryproducer.service;

import com.example.inventoryproducer.model.Product;
import okhttp3.mockwebserver.MockResponse;
import okhttp3.mockwebserver.MockWebServer;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.test.StepVerifier;

import java.io.IOException;

public class InventoryClientTest {
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
    void fetchProducts_returnsItems() {
        String body = """
            [
              {"product_id":"p1","sku":"SKU-001","qty":10},
              {"product_id":"p2","sku":"SKU-002","qty":5}
            ]
        """;
        server.enqueue(new MockResponse().setResponseCode(200).setBody(body).addHeader("Content-Type", "application/json"));

        WebClient webClient = WebClient.builder().baseUrl(server.url("/").toString()).build();
        InventoryClient client = new InventoryClient(webClient);

        StepVerifier.create(client.fetchProducts())
            .expectNextMatches(p -> p instanceof Product && ((Product)p).getProduct_id().equals("p1"))
            .expectNextMatches(p -> p instanceof Product && ((Product)p).getProduct_id().equals("p2"))
            .verifyComplete();
    }
}
