HTTP Server from Scratch - Python Implementation

This project implements a basic, low-level HTTP/1.1 server using only Python's standard library networking primitives (socket). It utilizes threading for concurrent connection handling.

1. Setup and Run Instructions

Prerequisites

Python 3.8+ (Required for modern datetime API)

Running the Server

Run the server from your terminal. You can specify a port (optional):

python http_server.py 8080
# Server will start on [http://127.0.0.1:8080](http://127.0.0.1:8080)


2. Supported Endpoints and Method Summary

The server manages a persistent, in-memory JSON data store (DATA_STORE).

| Method | Path     | Description                                                          | Expected Status             |
|--------|----------|----------------------------------------------------------------------|-----------------------------|
| GET    | /        | Returns a welcome message.                                           | 200 OK                      |
| GET    | /echo?   | Echoes back the value of the `message` query parameter.              | 200 OK (or 400 Bad Request) |
| POST   | /data    | Accepts JSON, assigns a unique ID, stores, and returns item.         | 201 Created                 |
| GET    | /data    | Returns all stored data as a JSON array.                             | 200 OK                      |
| GET    | /data/:id| Returns a specific item by ID.                                       | 200 OK (or 404 Not Found)   |
| PUT    | /data/:id| Replaces an existing item. Requires `Content-Type: application/json`.| 200 OK (or 404 Not Found)   |



3. Design Decisions and Architecture Overview

Low-Level HTTP Implementation
Request Parsing: The read_full_request function ensures complete extraction of headers and large JSON bodies.

Response Formatting: The generate_response helper centralizes all protocol requirements (Status Line, Date, Content-Length, Connection: close) to ensure valid HTTP/1.1 replies.

Routing: The custom find_handler function handles both static paths and variable paths (/data/:id), isolating the resource ID for use by the handler.

Concurrency and Thread Safety

Concurrency Model: Implemented using Python's threading module. For every accepted connection, a new thread is spawned to run handle_client_connection. This prevents blocking and is essential for meeting the high concurrency requirements.

Thread Safety: All access to the shared, mutable state (DATA_STORE and NEXT_ID) is protected by a threading.Lock object (LOCK). This prevents race conditions and data corruption during simultaneous write operations (POST, PUT).

4. Implemented Bonus Features

Concurrent request handling: Implemented and tested with threading.Thread.

Request logging middleware: The handle_client_connection function logs the timestamp, method, path, status code, and client address for every request.