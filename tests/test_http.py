import json
import threading
from concurrent.futures import ThreadPoolExecutor
from urllib.request import Request, urlopen

from werkzeug.serving import make_server

from .support import ApiTestCase


class HttpTests(ApiTestCase):
    def test_api_over_real_http(self):
        server = make_server("127.0.0.1", 0, self.app)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_port}/api/v1"
        try:
            with urlopen(base + "/health", timeout=5) as response:
                self.assertEqual(json.load(response), {"status": "ok"})
            request = Request(
                base + "/decisions", data=json.dumps(self.payload()).encode("utf-8"),
                headers={"Content-Type": "application/json"}, method="POST",
            )
            with urlopen(request, timeout=5) as response:
                self.assertEqual(response.status, 201)
                decision = json.load(response)
            request = Request(
                base + f"/decisions/{decision['id']}/approve", data=b"{}",
                headers={"Content-Type": "application/json"}, method="POST",
            )
            with urlopen(request, timeout=5) as response:
                self.assertEqual(json.load(response)["status"], "accepted")
        finally:
            server.shutdown()
            thread.join(timeout=5)
            server.server_close()

    def test_concurrent_partial_updates_do_not_lose_changes(self):
        decision = self.decision()
        barrier = threading.Barrier(2)

        def update(data):
            client = self.app.test_client()
            barrier.wait(timeout=5)
            return client.patch(f"/api/v1/decisions/{decision['id']}", json=data).status_code

        with ThreadPoolExecutor(max_workers=2) as executor:
            first = executor.submit(update, {"title": "Updated title"})
            second = executor.submit(update, {"context": "Updated context"})
            self.assertEqual(first.result(timeout=15), 200)
            self.assertEqual(second.result(timeout=15), 200)
        final = self.get(f"/decisions/{decision['id']}")
        self.assertEqual(final["title"], "Updated title")
        self.assertEqual(final["context"], "Updated context")
