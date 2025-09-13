# Java Producers (Spring Boot)

Modules to implement:
- crm-producer: fetches customers via REST/SOAP and produces to topic `customer_data`.
- inventory-producer: fetches products via REST and produces to topic `inventory_data`.

Key libraries:
- Spring Boot 3, Spring WebFlux (WebClient), Resilience4j
- Spring for Apache Kafka (spring-kafka)

Config (env):
- KAFKA_BOOTSTRAP_SERVERS (default: localhost:29092)
- CRM_BASE_URL (default: http://localhost:8000)
- INVENTORY_BASE_URL (default: http://localhost:8000)

Build & run (placeholder):
```
./mvnw -pl crm-producer -am spring-boot:run
./mvnw -pl inventory-producer -am spring-boot:run
```
