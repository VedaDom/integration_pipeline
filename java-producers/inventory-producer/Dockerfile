# Build stage
FROM maven:3.9-eclipse-temurin-17 AS builder
WORKDIR /workspace
# Copy entire multi-module project to build this module with parent
COPY .. /workspace
RUN mvn -q -f java-producers/pom.xml -pl inventory-producer -am -DskipTests package

# Run stage
FROM eclipse-temurin:17-jre
WORKDIR /app
# Copy built jar
COPY --from=builder /workspace/java-producers/inventory-producer/target/inventory-producer-0.0.1-SNAPSHOT.jar /app/app.jar
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
# Add JMX Exporter (Prometheus) for Kafka client metrics
RUN mkdir -p /app/jmx && \
    curl -fsSL -o /app/jmx/jmx_prometheus_javaagent.jar https://repo1.maven.org/maven2/io/prometheus/jmx/jmx_prometheus_javaagent/0.20.0/jmx_prometheus_javaagent-0.20.0.jar
COPY ../../infrastructure/jmx/kafka_client.yml /app/jmx/kafka_client.yml
ENV JAVA_TOOL_OPTIONS="-javaagent:/app/jmx/jmx_prometheus_javaagent.jar=9404:/app/jmx/kafka_client.yml"
ENV JAVA_OPTS="-XX:+UseG1GC -XX:MaxRAMPercentage=75.0"
EXPOSE 8082 9404
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar /app/app.jar"]
