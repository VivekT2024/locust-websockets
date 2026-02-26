# locust-websockets

A minimal Spring Boot application that exposes WebSocket endpoints.

## Endpoints

- Raw WebSocket echo endpoint: `ws://localhost:8080/ws/echo`
- STOMP endpoint: `ws://localhost:8080/ws/stomp`
  - Send messages to: `/app/chat`
  - Subscribe to: `/topic/messages`

## Run

```bash
mvn spring-boot:run
```

## Build and test

```bash
mvn test
```
