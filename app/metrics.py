from collections import defaultdict
import time

http_requests_total = defaultdict(int)
webhook_requests_total = defaultdict(int)


class Timer:
    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *_):
        self.ms = int((time.time() - self.start) * 1000)
        
def render_metrics() -> str:
    lines = []

    for (path, status), count in http_requests_total.items():
        lines.append(
            f'http_requests_total{{path="{path}",status="{status}"}} {count}'
        )

    for result, count in webhook_requests_total.items():
        lines.append(
            f'webhook_requests_total{{result="{result}"}} {count}'
        )

    return "\n".join(lines) + "\n"

