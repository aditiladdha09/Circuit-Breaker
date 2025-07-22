# 🔌 Circuit Breaker Pattern in Python

A simple yet effective implementation of the **Circuit Breaker** pattern written in Python, inspired by resilience libraries like Resilience4j.

---

## 📌 What is a Circuit Breaker?

In distributed systems, repeated calls to a failing service can lead to cascading failures.  
A **Circuit Breaker**:
- Monitors calls to a service,
- Trips to an `OPEN` state when failures exceed a threshold,
- Blocks further calls while giving the service time to recover,
- Switches to a `HALF_OPEN` state to test recovery,
- Returns to `CLOSED` when things are healthy again.

This prevents wasting resources on doomed calls and improves system resilience.

---

## 🚀 Features

✅ **3 states implemented**:
- `CLOSED`: Normal operation, calls pass through.
- `OPEN`: Calls are blocked and fail fast.
- `HALF_OPEN`: Limited test calls allowed to probe recovery.

✅ **Configurable parameters**:
- `failure_rate_threshold`: % failures to trip to OPEN.
- `window_size`: Sliding window of recent calls to monitor.
- `half_open_max_calls`: Number of test calls in HALF_OPEN.
- `open_state_wait`: Seconds to wait before moving from OPEN to HALF_OPEN.

✅ **Sliding window for recent calls**:
- Keeps track of successes/failures efficiently.

✅ **Easy to integrate**:
- Wrap your function calls with `cb.call()`.

✅ **Clear logging of state transitions**:
- Prints `[TRANSITION] → OPEN`, `→ HALF_OPEN`, `→ CLOSED`.

---

## 📂 Project Structure

circuit_breaker/
├── circuit_breaker.py # Main implementation with demo
├── README.md # This file
└── requirements.txt # Dependencies (none needed beyond stdlib)
