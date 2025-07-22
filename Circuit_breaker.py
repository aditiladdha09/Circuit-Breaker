import time
from collections import deque
from enum import Enum

# ------------------------
# STATES
# ------------------------
# The Circuit Breaker can be in one of these states at any time:
# CLOSED     → Normal operation, all calls go through.
# OPEN       → Calls are blocked because failure rate exceeded threshold.
# HALF_OPEN  → Limited test calls are allowed to check if system has recovered.
class State(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


# ------------------------
# CIRCUIT BREAKER CLASS
# ------------------------
class CircuitBreaker:
    def __init__(self,
                 failure_rate_threshold=50,  # percentage of failures to trip breaker
                 window_size=4,               # how many recent calls to track
                 half_open_max_calls=2,       # test calls in half-open state
                 open_state_wait=3):          # wait seconds before moving from OPEN → HALF_OPEN
        # Configuration values
        self.failure_rate_threshold = failure_rate_threshold
        self.window_size = window_size
        self.half_open_max_calls = half_open_max_calls
        self.open_state_wait = open_state_wait

        # Internal state
        self.state = State.CLOSED                   # initial state
        self.last_failure_time = None               # when we entered OPEN state
        self.recent_calls = deque(maxlen=window_size)  # sliding window of recent call results

        # HALF_OPEN state tracking
        self.half_open_calls = 0
        self.half_open_success = 0

    # ------------------------
    # Calculate failure rate of recent calls
    def _current_failure_rate(self):
        if not self.recent_calls:
            return 0.0
        failures = self.recent_calls.count(False)  # count failed calls
        return (failures / len(self.recent_calls)) * 100

    # ------------------------
    # Transition helpers
    def _transition_to_open(self):
        self.state = State.OPEN
        self.last_failure_time = time.time()  # record when it tripped
        print("[TRANSITION] → OPEN")

    def _transition_to_half_open(self):
        self.state = State.HALF_OPEN
        self.half_open_calls = 0
        self.half_open_success = 0
        print("[TRANSITION] → HALF_OPEN")

    def _transition_to_closed(self):
        self.state = State.CLOSED
        self.recent_calls.clear()  # reset history
        print("[TRANSITION] → CLOSED")

    # ------------------------
    # Main entrypoint: Call a function through the breaker
    def call(self, func, *args, **kwargs):
        # BEFORE EXECUTION: check state rules
        if self.state == State.OPEN:
            # Check if enough time has passed to move to HALF_OPEN
            if (time.time() - self.last_failure_time) >= self.open_state_wait:
                self._transition_to_half_open()
            else:
                raise Exception("CallNotPermittedException (Circuit is OPEN)")

        # In HALF_OPEN, only allow limited test calls
        if self.state == State.HALF_OPEN and self.half_open_calls >= self.half_open_max_calls:
            raise Exception("CallNotPermittedException (Too many test calls in HALF_OPEN)")

        # EXECUTE THE FUNCTION
        try:
            result = func(*args, **kwargs)  # run backend service
            self._on_success()               # record success
            return result
        except Exception as e:
            self._on_failure()               # record failure
            raise e

    # ------------------------
    # Handle success result
    def _on_success(self):
        if self.state == State.HALF_OPEN:
            # In HALF_OPEN, track how many calls succeed
            self.half_open_calls += 1
            self.half_open_success += 1
            # If all allowed test calls succeeded, system is healthy again
            if (self.half_open_calls >= self.half_open_max_calls and
                    self.half_open_success == self.half_open_calls):
                self._transition_to_closed()
        else:
            # In CLOSED, record a successful call in the sliding window
            self.recent_calls.append(True)
            # If even after success our failure rate exceeds threshold, trip
            if self._current_failure_rate() > self.failure_rate_threshold:
                self._transition_to_open()

    # ------------------------
    # Handle failure result
    def _on_failure(self):
        if self.state == State.HALF_OPEN:
            # Any failure in HALF_OPEN trips back to OPEN
            self.half_open_calls += 1
            self._transition_to_open()
        else:
            # Record failure in sliding window
            self.recent_calls.append(False)
            # If failure rate too high, trip to OPEN
            if self._current_failure_rate() > self.failure_rate_threshold:
                self._transition_to_open()


# ------------------------
# DEMO SERVICE
# ------------------------
# This represents a backend service. It succeeds by default,
# but if you pass should_fail=True, it throws an exception.
def unstable_service(should_fail=False):
    if should_fail:
        raise Exception("Service failed!")
    return "Success!"


# ------------------------
# TESTING THE BREAKER
# ------------------------
if __name__ == "__main__":
    # Create breaker with thresholds
    cb = CircuitBreaker(
        failure_rate_threshold=50,
        window_size=4,
        half_open_max_calls=2,
        open_state_wait=3
    )

    print("\n--- Initial calls ---")
    # 1. Normal success (CLOSED)
    try:
        print(cb.call(unstable_service, False))  # success
    except Exception as e:
        print(e)

    # 2. One failure (still under threshold)
    try:
        print(cb.call(unstable_service, True))   # fail
    except Exception as e:
        print(e)

    # 3. Another failure (2 failures in 3 calls → failure rate > 50% → trips to OPEN)
    try:
        print(cb.call(unstable_service, True))
    except Exception as e:
        print(e)

    # 4. Call while OPEN (should be blocked)
    try:
        print(cb.call(unstable_service, False))
    except Exception as e:
        print(e)

    print("\n--- Waiting to move to HALF_OPEN ---")
    # Wait enough time to allow HALF_OPEN state
    time.sleep(4)

    # 5. Test calls in HALF_OPEN
    try:
        print(cb.call(unstable_service, False))  # test success
    except Exception as e:
        print(e)
    try:
        print(cb.call(unstable_service, False))  # second success → transitions to CLOSED
    except Exception as e:
        print(e)

    print("\n--- After recovery ---")
    # 6. After recovery, circuit is CLOSED, calls go through
    try:
        print(cb.call(unstable_service, False))
    except Exception as e:
        print(e)
