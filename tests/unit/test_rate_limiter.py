"""
rate_limiter模块单元测试
"""
import time
import pytest
import requests
from unittest.mock import MagicMock, patch
from src.utils.rate_limiter import (
    TokenBucketRateLimiter,
    APIRetryConfig,
    RateLimitedAPIClient,
    create_rate_limited_client,
    DEFAULT_RATE_LIMITS,
)


class TestTokenBucketRateLimiter:
    def test_acquire_immediately_when_tokens_available(self):
        limiter = TokenBucketRateLimiter(rate=10.0, capacity=10, name="test")
        assert limiter.acquire(timeout=1.0) is True

    def test_acquire_waits_when_no_tokens(self):
        limiter = TokenBucketRateLimiter(rate=10.0, capacity=1, name="test")
        assert limiter.acquire(timeout=1.0) is True
        assert limiter.acquire(timeout=1.0) is True

    def test_acquire_timeout(self):
        limiter = TokenBucketRateLimiter(rate=0.01, capacity=0, name="test")
        limiter.tokens = 0.0
        result = limiter.acquire(timeout=0.1)
        assert result is False

    def test_wait_and_acquire_raises_on_timeout(self):
        limiter = TokenBucketRateLimiter(rate=0.01, capacity=0, name="test")
        limiter.tokens = 0.0
        with patch.object(limiter, 'acquire', return_value=False):
            with pytest.raises(RuntimeError, match="获取令牌超时"):
                limiter.wait_and_acquire()

    def test_tokens_refill_over_time(self):
        limiter = TokenBucketRateLimiter(rate=100.0, capacity=10, name="test")
        limiter.acquire()
        limiter.acquire()
        time.sleep(0.05)
        assert limiter.acquire(timeout=0.5) is True

    def test_capacity_limits_tokens(self):
        limiter = TokenBucketRateLimiter(rate=1000.0, capacity=2, name="test")
        time.sleep(0.01)
        limiter._refill()
        assert limiter.tokens <= 2.0

    def test_default_rate_limits_exist(self):
        assert "coingecko" in DEFAULT_RATE_LIMITS
        assert "glassnode" in DEFAULT_RATE_LIMITS
        assert "coinmetrics" in DEFAULT_RATE_LIMITS
        assert "fear_greed" in DEFAULT_RATE_LIMITS
        assert "cryptoquant" in DEFAULT_RATE_LIMITS
        assert "telegram" in DEFAULT_RATE_LIMITS


class TestAPIRetryConfig:
    def test_default_config(self):
        config = APIRetryConfig()
        assert config.max_retries == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 30.0
        assert config.backoff_factor == 2.0
        assert 429 in config.retryable_status_codes

    def test_get_delay_exponential_backoff(self):
        config = APIRetryConfig(base_delay=1.0, backoff_factor=2.0)
        assert config.get_delay(0) == 1.0
        assert config.get_delay(1) == 2.0
        assert config.get_delay(2) == 4.0

    def test_get_delay_capped_at_max(self):
        config = APIRetryConfig(base_delay=1.0, backoff_factor=10.0, max_delay=5.0)
        assert config.get_delay(0) == 1.0
        assert config.get_delay(1) == 5.0
        assert config.get_delay(2) == 5.0


class TestRateLimitedAPIClient:
    def _make_response(self, status_code=200, headers=None, json_data=None):
        resp = MagicMock(spec=requests.Response)
        resp.status_code = status_code
        resp.headers = headers or {}
        resp.json.return_value = json_data or {}
        resp.raise_for_status.side_effect = (
            requests.exceptions.HTTPError() if status_code >= 400 else None
        )
        return resp

    def test_successful_request(self):
        client = RateLimitedAPIClient()
        mock_resp = self._make_response(200)
        with patch.object(client.session, 'request', return_value=mock_resp):
            result = client.request("GET", "http://test.com")
            assert result.status_code == 200

    def test_retry_on_429(self):
        client = RateLimitedAPIClient(retry_config=APIRetryConfig(max_retries=2, base_delay=0.01))
        resp_429 = self._make_response(429)
        resp_200 = self._make_response(200)
        with patch.object(client.session, 'request', side_effect=[resp_429, resp_200]):
            result = client.request("GET", "http://test.com")
            assert result.status_code == 200

    def test_retry_on_server_error(self):
        client = RateLimitedAPIClient(retry_config=APIRetryConfig(max_retries=2, base_delay=0.01))
        resp_500 = self._make_response(500)
        resp_200 = self._make_response(200)
        with patch.object(client.session, 'request', side_effect=[resp_500, resp_200]):
            result = client.request("GET", "http://test.com")
            assert result.status_code == 200

    def test_raises_after_max_retries_on_429(self):
        client = RateLimitedAPIClient(retry_config=APIRetryConfig(max_retries=2, base_delay=0.01))
        resp_429 = self._make_response(429)
        with patch.object(client.session, 'request', return_value=resp_429):
            with pytest.raises(requests.exceptions.HTTPError):
                client.request("GET", "http://test.com")

    def test_retry_on_connection_error(self):
        client = RateLimitedAPIClient(retry_config=APIRetryConfig(max_retries=2, base_delay=0.01))
        resp_200 = self._make_response(200)
        with patch.object(
            client.session, 'request',
            side_effect=[requests.exceptions.ConnectionError("conn fail"), resp_200]
        ):
            result = client.request("GET", "http://test.com")
            assert result.status_code == 200

    def test_raises_after_max_retries_on_connection_error(self):
        client = RateLimitedAPIClient(retry_config=APIRetryConfig(max_retries=2, base_delay=0.01))
        with patch.object(
            client.session, 'request',
            side_effect=requests.exceptions.ConnectionError("conn fail")
        ):
            with pytest.raises(requests.exceptions.ConnectionError):
                client.request("GET", "http://test.com")

    def test_rate_limiter_called_before_request(self):
        limiter = TokenBucketRateLimiter(rate=10.0, capacity=10, name="test")
        client = RateLimitedAPIClient(rate_limiter=limiter)
        mock_resp = self._make_response(200)
        with patch.object(client.session, 'request', return_value=mock_resp):
            with patch.object(limiter, 'wait_and_acquire') as mock_acquire:
                client.request("GET", "http://test.com")
                assert mock_acquire.call_count >= 1

    def test_retry_after_header_respected(self):
        client = RateLimitedAPIClient(retry_config=APIRetryConfig(max_retries=2, base_delay=0.01))
        resp_429 = self._make_response(429, headers={"Retry-After": "0.01"})
        resp_200 = self._make_response(200)
        with patch.object(client.session, 'request', side_effect=[resp_429, resp_200]):
            result = client.request("GET", "http://test.com")
            assert result.status_code == 200

    def test_get_and_post_convenience_methods(self):
        client = RateLimitedAPIClient()
        mock_resp = self._make_response(200)
        with patch.object(client, 'request', return_value=mock_resp) as mock_req:
            client.get("http://test.com")
            client.post("http://test.com", json={"key": "val"})
            assert mock_req.call_count == 2


class TestCreateRateLimitedClient:
    def test_creates_client_with_custom_rate(self):
        client = create_rate_limited_client("test", rate=5.0, capacity=3)
        assert client.rate_limiter is not None
        assert client.rate_limiter.rate == 5.0
        assert client.rate_limiter.capacity == 3

    def test_creates_client_from_defaults(self):
        client = create_rate_limited_client("coingecko")
        assert client.rate_limiter is not None
        assert client.rate_limiter.name == "coingecko"

    def test_creates_client_without_limiter(self):
        client = create_rate_limited_client("unknown_api")
        assert client.rate_limiter is None

    def test_custom_retry_config(self):
        client = create_rate_limited_client("test", rate=1.0, max_retries=5, base_delay=2.0)
        assert client.retry_config.max_retries == 5
        assert client.retry_config.base_delay == 2.0
