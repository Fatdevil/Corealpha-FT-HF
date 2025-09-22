import math
import time

import pytest

from corealpha_adapter.providers import FinGPTProvider
from corealpha_adapter.schemas import SummarizeRequest


@pytest.mark.slow
@pytest.mark.asyncio
async def test_summarize_smoke_load_p95_under_800ms():
    provider = FinGPTProvider(
        base_url="",
        api_key="",
        timeout=0.1,
        max_retries=0,
        cache_ttl_seconds=0,
        use_stub_summary=True,
        use_stub_sentiment=True,
        voting_engine=None,
        client=None,
    )

    durations = []
    for idx in range(50):
        start = time.perf_counter()
        await provider.summarize(SummarizeRequest(text=f"Load test message {idx}"))
        durations.append((time.perf_counter() - start) * 1000)

    durations.sort()
    percentile_index = max(0, math.ceil(0.95 * len(durations)) - 1)
    p95 = durations[percentile_index]

    assert p95 < 800

    await provider.aclose()
