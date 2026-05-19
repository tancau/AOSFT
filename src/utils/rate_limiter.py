"""
API限流与重试工具
提供令牌桶限流、指数退避重试、HTTP 429专用处理
"""
import time
import logging
import threading
from typing import Optional, Callable, Any
from functools import wraps
import requests

logger = logging.getLogger("aosft")


class TokenBucketRateLimiter:
    def __init__(
        self,
        rate: float,
        capacity: Optional[int] = None,
        name: str = "default"
    ):
        self.rate = rate
        self.capacity = capacity or max(1, int(rate))
        self.tokens = float(self.capacity)
        self.last_refill = time.monotonic()
        self.name = name
        self._lock = threading.Lock()

    def _refill(self):
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_refill = now

    def acquire(self, timeout: float = 60.0) -> bool:
        deadline = time.monotonic() + timeout
        while True:
            with self._lock:
                self._refill()
                if self.tokens >= 1.0:
                    self.tokens -= 1.0
                    return True
                wait = (1.0 - self.tokens) / self.rate

            remaining = deadline - time.monotonic()
            if remaining <= 0:
                logger.warning(f"[RateLimiter:{self.name}] 获取令牌超时")
                return False
            time.sleep(min(wait, remaining, 1.0))

    def wait_and_acquire(self):
        if not self.acquire(timeout=120.0):
            raise RuntimeError(f"RateLimiter '{self.name}' 获取令牌超时")


class APIRetryConfig:
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        backoff_factor: float = 2.0,
        retryable_status_codes: Optional[tuple] = None
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.retryable_status_codes = retryable_status_codes or (429, 500, 502, 503, 504)

    def get_delay(self, attempt: int) -> float:
        delay = self.base_delay * (self.backoff_factor ** attempt)
        return min(delay, self.max_delay)


class RateLimitedAPIClient:
    def __init__(
        self,
        rate_limiter: Optional[TokenBucketRateLimiter] = None,
        retry_config: Optional[APIRetryConfig] = None,
        session: Optional[requests.Session] = None
    ):
        self.rate_limiter = rate_limiter
        self.retry_config = retry_config or APIRetryConfig()
        self.session = session or requests.Session()

    def request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> requests.Response:
        if self.rate_limiter:
            self.rate_limiter.wait_and_acquire()

        last_exception = None
        for attempt in range(self.retry_config.max_retries):
            try:
                resp = self.session.request(method, url, **kwargs)

                if resp.status_code == 429:
                    retry_after = self._parse_retry_after(resp)
                    delay = retry_after or self.retry_config.get_delay(attempt)
                    logger.warning(
                        f"HTTP 429 Too Many Requests, "
                        f"等待{delay:.1f}s后重试(尝试{attempt+1}/{self.retry_config.max_retries})"
                    )
                    if attempt < self.retry_config.max_retries - 1:
                        time.sleep(delay)
                        if self.rate_limiter:
                            self.rate_limiter.wait_and_acquire()
                        continue
                    resp.raise_for_status()

                if resp.status_code in self.retry_config.retryable_status_codes:
                    delay = self.retry_config.get_delay(attempt)
                    logger.warning(
                        f"HTTP {resp.status_code}, "
                        f"等待{delay:.1f}s后重试(尝试{attempt+1}/{self.retry_config.max_retries})"
                    )
                    if attempt < self.retry_config.max_retries - 1:
                        time.sleep(delay)
                        if self.rate_limiter:
                            self.rate_limiter.wait_and_acquire()
                        continue
                    resp.raise_for_status()

                resp.raise_for_status()
                return resp

            except requests.exceptions.ConnectionError as e:
                last_exception = e
                delay = self.retry_config.get_delay(attempt)
                logger.warning(
                    f"连接错误: {e}, "
                    f"等待{delay:.1f}s后重试(尝试{attempt+1}/{self.retry_config.max_retries})"
                )
                if attempt < self.retry_config.max_retries - 1:
                    time.sleep(delay)
                else:
                    raise

            except requests.exceptions.Timeout as e:
                last_exception = e
                delay = self.retry_config.get_delay(attempt)
                logger.warning(
                    f"请求超时: {e}, "
                    f"等待{delay:.1f}s后重试(尝试{attempt+1}/{self.retry_config.max_retries})"
                )
                if attempt < self.retry_config.max_retries - 1:
                    time.sleep(delay)
                else:
                    raise

            except requests.exceptions.HTTPError:
                raise

        raise last_exception or requests.exceptions.RequestException(
            f"重试{self.retry_config.max_retries}次后仍失败"
        )

    def get(self, url: str, **kwargs) -> requests.Response:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs) -> requests.Response:
        return self.request("POST", url, **kwargs)

    @staticmethod
    def _parse_retry_after(resp: requests.Response) -> Optional[float]:
        retry_after = resp.headers.get("Retry-After")
        if retry_after:
            try:
                return float(retry_after)
            except ValueError:
                pass
        return None


DEFAULT_RATE_LIMITS = {
    "coingecko": TokenBucketRateLimiter(rate=0.5, capacity=1, name="coingecko"),
    "fear_greed": TokenBucketRateLimiter(rate=1.0, capacity=2, name="fear_greed"),
    "glassnode": TokenBucketRateLimiter(rate=1.0, capacity=3, name="glassnode"),
    "cryptoquant": TokenBucketRateLimiter(rate=1.0, capacity=3, name="cryptoquant"),
    "coinmetrics": TokenBucketRateLimiter(rate=1.0, capacity=5, name="coinmetrics"),
    "telegram": TokenBucketRateLimiter(rate=0.5, capacity=1, name="telegram"),
}


def create_rate_limited_client(
    name: str,
    rate: Optional[float] = None,
    capacity: Optional[int] = None,
    max_retries: int = 3,
    base_delay: float = 1.0,
    session: Optional[requests.Session] = None
) -> RateLimitedAPIClient:
    if rate is not None:
        limiter = TokenBucketRateLimiter(
            rate=rate,
            capacity=capacity or max(1, int(rate)),
            name=name
        )
    elif name in DEFAULT_RATE_LIMITS:
        limiter = DEFAULT_RATE_LIMITS[name]
    else:
        limiter = None

    retry_config = APIRetryConfig(max_retries=max_retries, base_delay=base_delay)
    return RateLimitedAPIClient(
        rate_limiter=limiter,
        retry_config=retry_config,
        session=session
    )
