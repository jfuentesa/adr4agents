import asyncio
import json
import socket
from http.client import HTTPException
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen


class ApiError(Exception):
    def __init__(self, message, *, status=None, details=None):
        super().__init__(message)
        self.status = status
        self.details = details


class ApiClient:
    def __init__(self, base_url, timeout=15):
        parsed = urlsplit(base_url)
        if (parsed.scheme not in {"http", "https"} or not parsed.hostname
                or parsed.port == 0 or parsed.query or parsed.fragment or parsed.username or parsed.password):
            raise ValueError("API URL must be an HTTP(S) URL without credentials, query or fragment.")
        if not 0 < timeout <= 300:
            raise ValueError("API timeout must be between 0 and 300 seconds.")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def request(self, method, path, *, query=None, data=None):
        return await asyncio.to_thread(self._request, method, path, query=query, data=data)

    def _request(self, method, path, *, query=None, data=None):
        url = self.base_url + path
        parameters = {key: value for key, value in (query or {}).items() if value is not None}
        if parameters:
            url += "?" + urlencode(parameters)
        headers = {"Accept": "application/json"}
        payload = None
        if data is not None:
            payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = Request(url, data=payload, headers=headers, method=method)
        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw = response.read()
        except HTTPError as error:
            try:
                details = json.loads(error.read())
            except (ValueError, UnicodeDecodeError):
                details = {"error": {"code": "http_error", "message": error.reason}}
            finally:
                error.close()
            raise ApiError(f"API returned HTTP {error.code}.", status=error.code, details=details) from error
        except (URLError, TimeoutError, socket.timeout, HTTPException, OSError) as error:
            raise ApiError("Cannot reach the ADR4agents API. Check that it is running and accessible.") from error
        try:
            result = json.loads(raw)
        except (ValueError, UnicodeDecodeError) as error:
            raise ApiError("The API returned invalid JSON.") from error
        if not isinstance(result, dict):
            raise ApiError("The API response must be a JSON object.")
        return result
