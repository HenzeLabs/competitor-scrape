# rate_limit.py
import time
import threading
import time
import threading
from typing import Optional

class RateLimiter:
    """
    Simple thread-safe rate limiter using the token bucket algorithm.
    """
    def __init__(self, rate: float, per: float = 1.0):
        """
        :param rate: Number of tokens (requests) allowed per time window.
        :param per: Length of the time window in seconds.
        """
        self.rate = rate
        self.per = per
        self.allowance = rate
        self.last_check = time.monotonic()
        self.lock = threading.Lock()

    def acquire(self, tokens: float = 1) -> None:
        """
        Blocks until the requested number of tokens are available.
        :param tokens: Number of tokens to acquire.
        """
        while True:
            with self.lock:
                current = time.monotonic()
                time_passed = current - self.last_check
                self.last_check = current
                self.allowance += time_passed * (self.rate / self.per)
                if self.allowance > self.rate:
                    self.allowance = self.rate
                if self.allowance >= tokens:
                    self.allowance -= tokens
                    return
            time.sleep(0.01)

    def try_acquire(self, tokens: float = 1) -> bool:
        """
        Attempts to acquire tokens without blocking. Returns True if successful.
        :param tokens: Number of tokens to acquire.
        """
        with self.lock:
            current = time.monotonic()
            time_passed = current - self.last_check
            self.last_check = current
            self.allowance += time_passed * (self.rate / self.per)
            if self.allowance > self.rate:
                self.allowance = self.rate
            if self.allowance >= tokens:
                self.allowance -= tokens
                return True
            return False
