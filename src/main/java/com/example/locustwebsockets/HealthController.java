package com.example.locustwebsockets;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
public class HealthController {

    @GetMapping("/")
    public Map<String, String> index() {
        return Map.of(
                "status", "ok",
                "echoEndpoint", "ws://localhost:8080/ws/echo",
                "stompEndpoint", "ws://localhost:8080/ws/stomp"
        );
    }
}
