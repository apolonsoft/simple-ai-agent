#!/usr/bin/env python3
"""
High-Concurrency Benchmark & Load Testing Tool (Task S-2)
Simulates concurrent multi-tenant user journeys against the FastAPI backend:
1. User registration & JWT authentication
2. Thread creation (POST /api/v1/chats)
3. Multi-turn real-time SSE streaming (POST /api/v1/chats/{id}/stream)
4. Message history verification (GET /api/v1/chats/{id}/messages)
5. Thread deletion & Redis cache invalidation (DELETE /api/v1/chats/{id})

Reports: Success rate, Throughput (req/s, tokens/s), Latency percentiles (p50, p90, p95, p99).
"""
import argparse
import asyncio
import math
import sys
import time
import uuid
from dataclasses import dataclass, field
from typing import List, Optional
import httpx


@dataclass
class MetricBucket:
    name: str
    latencies_ms: List[float] = field(default_factory=list)
    success_count: int = 0
    failure_count: int = 0

    def record(self, latency_ms: float, success: bool):
        if success:
            self.success_count += 1
            self.latencies_ms.append(latency_ms)
        else:
            self.failure_count += 1

    def percentile(self, p: float) -> float:
        if not self.latencies_ms:
            return 0.0
        sorted_data = sorted(self.latencies_ms)
        k = (len(sorted_data) - 1) * (p / 100.0)
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return sorted_data[int(k)]
        return sorted_data[int(f)] * (c - k) + sorted_data[int(c)] * (k - f)

    @property
    def avg_ms(self) -> float:
        return sum(self.latencies_ms) / len(self.latencies_ms) if self.latencies_ms else 0.0

    @property
    def min_ms(self) -> float:
        return min(self.latencies_ms) if self.latencies_ms else 0.0

    @property
    def max_ms(self) -> float:
        return max(self.latencies_ms) if self.latencies_ms else 0.0


class BenchmarkRunner:
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        concurrency: int = 20,
        turns_per_user: int = 3,
        timeout_seconds: float = 30.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.concurrency = concurrency
        self.turns_per_user = turns_per_user
        self.timeout = timeout_seconds

        # Metrics trackers
        self.auth_metrics = MetricBucket("User Auth & Login")
        self.session_metrics = MetricBucket("Session Creation")
        self.stream_ttfb_metrics = MetricBucket("SSE Time to First Token (TTFB)")
        self.stream_total_metrics = MetricBucket("SSE Total Stream Duration")
        self.history_metrics = MetricBucket("History Fetch")
        self.delete_metrics = MetricBucket("Session Deletion")

        self.total_tokens_received = 0
        self.start_time: float = 0.0
        self.end_time: float = 0.0

    async def simulate_user(self, user_index: int, client: httpx.AsyncClient):
        email = f"loadtest_user_{uuid.uuid4().hex[:8]}@example.com"
        password = "BenchmarkPassword123!"

        # 1. Register & Login
        t0 = time.perf_counter()
        token: Optional[str] = None
        try:
            reg_res = await client.post(
                f"{self.base_url}/api/v1/auth/register",
                json={"email": email, "password": password},
            )
            if reg_res.status_code in (200, 201):
                login_res = await client.post(
                    f"{self.base_url}/api/v1/auth/login",
                    data={"username": email, "password": password},
                )
                if login_res.status_code == 200:
                    token = login_res.json().get("access_token")
            
            elapsed = (time.perf_counter() - t0) * 1000.0
            self.auth_metrics.record(elapsed, token is not None)
        except Exception:
            self.auth_metrics.record((time.perf_counter() - t0) * 1000.0, False)
            return

        if not token:
            return

        headers = {"Authorization": f"Bearer {token}"}

        # 2. Create Chat Session
        t0 = time.perf_counter()
        session_id: Optional[str] = None
        try:
            res = await client.post(
                f"{self.base_url}/api/v1/chats",
                json={"title": f"Load Session {user_index}"},
                headers=headers,
            )
            elapsed = (time.perf_counter() - t0) * 1000.0
            if res.status_code == 201:
                session_id = res.json().get("id")
                self.session_metrics.record(elapsed, True)
            else:
                self.session_metrics.record(elapsed, False)
        except Exception:
            self.session_metrics.record((time.perf_counter() - t0) * 1000.0, False)
            return

        if not session_id:
            return

        # 3. Multi-turn Streaming Conversations
        for turn_idx in range(self.turns_per_user):
            prompt = f"Load test turn {turn_idx + 1} for user {user_index}. Explain high concurrency scaling."
            t_stream_start = time.perf_counter()
            first_token_time: Optional[float] = None
            received_tokens = 0
            stream_success = False

            try:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/v1/chats/{session_id}/stream",
                    json={"content": prompt},
                    headers=headers,
                    timeout=self.timeout,
                ) as stream_res:
                    if stream_res.status_code == 200:
                        async for chunk in stream_res.aiter_lines():
                            if not chunk:
                                continue
                            if first_token_time is None:
                                first_token_time = (time.perf_counter() - t_stream_start) * 1000.0
                                self.stream_ttfb_metrics.record(first_token_time, True)

                            if "event: chunk" in chunk or "content" in chunk:
                                received_tokens += 1
                            elif "event: done" in chunk:
                                stream_success = True

                        t_total = (time.perf_counter() - t_stream_start) * 1000.0
                        self.stream_total_metrics.record(t_total, stream_success)
                        self.total_tokens_received += received_tokens
                    else:
                        t_total = (time.perf_counter() - t_stream_start) * 1000.0
                        self.stream_total_metrics.record(t_total, False)
            except Exception:
                t_total = (time.perf_counter() - t_stream_start) * 1000.0
                self.stream_total_metrics.record(t_total, False)

        # 4. Fetch Message History
        t0 = time.perf_counter()
        try:
            res = await client.get(
                f"{self.base_url}/api/v1/chats/{session_id}/messages",
                headers=headers,
            )
            elapsed = (time.perf_counter() - t0) * 1000.0
            self.history_metrics.record(elapsed, res.status_code == 200)
        except Exception:
            self.history_metrics.record((time.perf_counter() - t0) * 1000.0, False)

        # 5. Delete Session (tests cache invalidation)
        t0 = time.perf_counter()
        try:
            res = await client.delete(
                f"{self.base_url}/api/v1/chats/{session_id}",
                headers=headers,
            )
            elapsed = (time.perf_counter() - t0) * 1000.0
            self.delete_metrics.record(elapsed, res.status_code == 200)
        except Exception:
            self.delete_metrics.record((time.perf_counter() - t0) * 1000.0, False)

    async def run(self) -> bool:
        print("=" * 80)
        print(f"🚀 Running High-Concurrency Benchmark against {self.base_url}")
        print(f"📊 Target Concurrency: {self.concurrency} concurrent virtual users")
        print(f"🔄 Turns per user: {self.turns_per_user} (Total streaming sessions: {self.concurrency * self.turns_per_user})")
        print("=" * 80)

        limits = httpx.Limits(max_connections=100, max_keepalive_connections=50)
        async with httpx.AsyncClient(limits=limits, timeout=self.timeout) as client:
            self.start_time = time.perf_counter()
            tasks = [self.simulate_user(i, client) for i in range(self.concurrency)]
            await asyncio.gather(*tasks)
            self.end_time = time.perf_counter()

        return self.print_report()

    def print_report(self) -> bool:
        total_wall_time = max(0.001, self.end_time - self.start_time)
        all_buckets = [
            self.auth_metrics,
            self.session_metrics,
            self.stream_ttfb_metrics,
            self.stream_total_metrics,
            self.history_metrics,
            self.delete_metrics,
        ]

        total_reqs = sum(b.success_count + b.failure_count for b in all_buckets)
        total_success = sum(b.success_count for b in all_buckets)
        success_rate = (total_success / total_reqs * 100.0) if total_reqs > 0 else 0.0
        rps = total_reqs / total_wall_time
        tokens_per_sec = self.total_tokens_received / total_wall_time

        print("\n" + "=" * 80)
        print("📈 BENCHMARK RESULTS SUMMARY")
        print("=" * 80)
        print(f"⏱️  Total Test Duration:       {total_wall_time:.2f} s")
        print(f"📦 Total HTTP Requests:        {total_reqs}")
        print(f"✅ Successful Operations:      {total_success}")
        print(f"❌ Failed Operations:          {total_reqs - total_success}")
        print(f"🎯 Global Success Rate:        {success_rate:.2f}% (Threshold: >= 99.0%)")
        print(f"⚡ Request Throughput:         {rps:.2f} req/s")
        print(f"💬 Token Throughput:           {tokens_per_sec:.2f} tokens/s ({self.total_tokens_received} total tokens)")
        print("-" * 80)

        header = f"{'Operation':<32} | {'Reqs':<6} | {'Succ%':<6} | {'Avg':<8} | {'p50':<8} | {'p95':<8} | {'p99':<8}"
        print(header)
        print("-" * 80)

        for b in all_buckets:
            total_op = b.success_count + b.failure_count
            pct = (b.success_count / total_op * 100.0) if total_op > 0 else 0.0
            print(
                f"{b.name:<32} | "
                f"{total_op:<6} | "
                f"{pct:>5.1f}% | "
                f"{b.avg_ms:>6.1f}ms | "
                f"{b.percentile(50):>6.1f}ms | "
                f"{b.percentile(95):>6.1f}ms | "
                f"{b.percentile(99):>6.1f}ms"
            )

        print("=" * 80)

        # Verification criteria:
        passed = True
        if success_rate < 99.0:
            print(f"❌ FAILURE: Success rate ({success_rate:.1f}%) is below 99.0% target.")
            passed = False
        else:
            print(f"✅ PASS: Success rate meets enterprise target (>= 99.0%).")

        # Non-LLM p95 latency check (auth, session create, history, delete)
        non_llm_p95 = max(
            self.session_metrics.percentile(95),
            self.history_metrics.percentile(95),
            self.delete_metrics.percentile(95),
        )
        if non_llm_p95 > 250.0:
            print(f"⚠️  WARNING: High p95 latency on transactional endpoints: {non_llm_p95:.1f}ms")
        else:
            print(f"✅ PASS: High-speed transactional p95 latency is healthy: {non_llm_p95:.1f}ms")

        print("=" * 80 + "\n")
        return passed


def main():
    parser = argparse.ArgumentParser(description="AI Agent High-Concurrency Load Tester")
    parser.add_argument("--url", default="http://localhost:8000", help="Base backend URL")
    parser.add_argument("--concurrency", type=int, default=20, help="Simultaneous concurrent users")
    parser.add_argument("--turns", type=int, default=3, help="Chat turns per simulated user")
    parser.add_argument("--timeout", type=float, default=30.0, help="HTTP timeout in seconds")
    args = parser.parse_args()

    runner = BenchmarkRunner(
        base_url=args.url,
        concurrency=args.concurrency,
        turns_per_user=args.turns,
        timeout_seconds=args.timeout,
    )

    success = asyncio.run(runner.run())
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
