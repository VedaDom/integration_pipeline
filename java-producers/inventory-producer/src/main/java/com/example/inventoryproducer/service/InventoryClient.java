package com.example.inventoryproducer.service;

import com.example.inventoryproducer.model.Product;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Flux;
import reactor.util.retry.Retry;

import java.time.Duration;
import java.util.concurrent.atomic.AtomicReference;
import org.springframework.http.HttpStatus;

@Service
public class InventoryClient {
    private final WebClient webClient;
    private final AtomicReference<String> etag = new AtomicReference<>(null);
    private final AtomicReference<String> lastModified = new AtomicReference<>(null);

    public InventoryClient(WebClient inventoryWebClient) {
        this.webClient = inventoryWebClient;
    }

    public Flux<Product> fetchProducts() {
        return webClient.get()
                .uri("/products")
                .headers(h -> {
                    String et = etag.get();
                    String lm = lastModified.get();
                    if (et != null) h.setIfNoneMatch(et);
                    if (lm != null) h.set("If-Modified-Since", lm);
                })
                .exchangeToFlux(resp -> {
                    if (resp.statusCode() == HttpStatus.NOT_MODIFIED) {
                        return Flux.empty();
                    }
                    resp.headers().asHttpHeaders().getOrEmpty("ETag").stream().findFirst().ifPresent(etag::set);
                    resp.headers().asHttpHeaders().getOrEmpty("Last-Modified").stream().findFirst().ifPresent(lastModified::set);
                    return resp.bodyToFlux(Product.class);
                })
                .retryWhen(Retry.backoff(3, Duration.ofMillis(500)).maxBackoff(Duration.ofSeconds(5)));
    }
}
