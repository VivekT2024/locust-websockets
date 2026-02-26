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

## Load test with Locust

1. Install dependencies:

```bash
pip install locust websocket-client
```

2. Start the Spring Boot app:

```bash
mvn spring-boot:run
```

3. Run Locust with the generated script:

```bash
locust -f locustfile.py
```

4. Open http://localhost:8089 and start a test.

### Optional environment variables

- `TARGET_HOST` (default: `localhost`)
- `TARGET_PORT` (default: `8080`)
- `TARGET_SCHEME` (default: `ws`)
- `STOMP_HOST` (default: `localhost`)

Example running headless:

```bash
TARGET_HOST=127.0.0.1 locust -f locustfile.py --headless -u 20 -r 5 -t 2m
```
