import json
import os
import time
import uuid
from contextlib import suppress

import gevent
from locust import User, between, events, task
from websocket import WebSocketTimeoutException, create_connection


def build_ws_url(path: str) -> str:
    host = os.getenv("TARGET_HOST", "localhost")
    port = os.getenv("TARGET_PORT", "8080")
    scheme = os.getenv("TARGET_SCHEME", "ws")
    return f"{scheme}://{host}:{port}{path}"


def stomp_frame(command: str, headers: dict[str, str] | None = None, body: str = "") -> str:
    headers = headers or {}
    header_blob = "\n".join(f"{k}:{v}" for k, v in headers.items())
    return f"{command}\n{header_blob}\n\n{body}\x00"


class EchoWebSocketUser(User):
    wait_time = between(0.2, 1.0)

    def on_start(self) -> None:
        self.url = build_ws_url("/ws/echo")
        self.ws = create_connection(self.url, timeout=5)

        start = time.perf_counter()
        greeting = self.ws.recv()
        response_time_ms = (time.perf_counter() - start) * 1000
        events.request.fire(
            request_type="WS",
            name="echo_connect_greeting",
            response_time=response_time_ms,
            response_length=len(greeting),
            exception=None,
        )

    @task
    def echo_round_trip(self) -> None:
        payload = f"ping-{uuid.uuid4().hex[:8]}"
        expected = f"echo: {payload}"
        start = time.perf_counter()

        try:
            self.ws.send(payload)
            message = self.ws.recv()
            if message != expected:
                raise AssertionError(f"unexpected echo payload: {message}")

            events.request.fire(
                request_type="WS",
                name="echo_message",
                response_time=(time.perf_counter() - start) * 1000,
                response_length=len(message),
                exception=None,
            )
        except Exception as exc:
            events.request.fire(
                request_type="WS",
                name="echo_message",
                response_time=(time.perf_counter() - start) * 1000,
                response_length=0,
                exception=exc,
            )

    def on_stop(self) -> None:
        with suppress(Exception):
            self.ws.close()


class StompWebSocketUser(User):
    wait_time = between(0.2, 1.0)

    def on_start(self) -> None:
        self.url = build_ws_url("/ws/stomp")
        self.ws = create_connection(self.url, timeout=5)
        self.subscription_id = uuid.uuid4().hex[:8]

        self.ws.send(
            stomp_frame(
                "CONNECT",
                {
                    "accept-version": "1.2",
                    "host": os.getenv("STOMP_HOST", "localhost"),
                    "heart-beat": "0,0",
                },
            )
        )

        start = time.perf_counter()
        connected = self.ws.recv()
        response_time_ms = (time.perf_counter() - start) * 1000
        exc = None if connected.startswith("CONNECTED") else AssertionError(connected)
        events.request.fire(
            request_type="STOMP",
            name="stomp_connect",
            response_time=response_time_ms,
            response_length=len(connected),
            exception=exc,
        )

        self.ws.send(
            stomp_frame(
                "SUBSCRIBE",
                {
                    "id": self.subscription_id,
                    "destination": "/topic/messages",
                    "ack": "auto",
                },
            )
        )

    @task
    def send_and_receive_chat_message(self) -> None:
        content = f"locust-{uuid.uuid4().hex[:8]}"
        payload = json.dumps({"from": "locust", "content": content})
        start = time.perf_counter()

        try:
            self.ws.send(
                stomp_frame(
                    "SEND",
                    {
                        "destination": "/app/chat",
                        "content-type": "application/json",
                    },
                    payload,
                )
            )

            timeout_at = time.time() + 5
            while time.time() < timeout_at:
                frame = self.ws.recv()
                if frame.startswith("MESSAGE") and content in frame:
                    events.request.fire(
                        request_type="STOMP",
                        name="stomp_chat_round_trip",
                        response_time=(time.perf_counter() - start) * 1000,
                        response_length=len(frame),
                        exception=None,
                    )
                    return

            raise WebSocketTimeoutException("timed out waiting for STOMP MESSAGE")
        except Exception as exc:
            events.request.fire(
                request_type="STOMP",
                name="stomp_chat_round_trip",
                response_time=(time.perf_counter() - start) * 1000,
                response_length=0,
                exception=exc,
            )

    def on_stop(self) -> None:
        with suppress(Exception):
            self.ws.send(stomp_frame("DISCONNECT", {"receipt": uuid.uuid4().hex[:8]}))
        gevent.sleep(0.05)
        with suppress(Exception):
            self.ws.close()
