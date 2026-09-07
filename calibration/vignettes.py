"""Phase 12 calibration seed: hand-scored vignette sessions (blind scores).

Each vignette is a fixed mini-transcript plus hand-built claims/evidence and
the author's own scores per rubric dimension, written BEFORE seeing the
evaluator's output. ``scratch/test_phase12_calibration.py`` rebuilds each
vignette as a real session, runs the evaluator, and reports agreement.
Keep this file stable — it becomes V3's meta-evaluation seed.
"""

from __future__ import annotations

VIGNETTES: list[dict] = [
    {
        "name": "strong senior",
        "turns": [
            ("miki", "How did you design cache invalidation?"),
            (
                "candidate",
                "Write-through with 5-minute TTL per key class; "
                "measured 92% hit rate via per-key counters over two weeks.",
            ),
            ("miki", "Why write-through over write-back here?"),
            (
                "candidate",
                "Write-back risked losing orders on crash, "
                "unacceptable for payments; we accepted 15% higher write load, "
                "verified with load tests at 3x peak before launch.",
            ),
        ],
        "claims": [
            {
                "turn": 2,
                "text": "92% hit rate measured via per-key counters.",
                "category": "performance",
                "confidence": 0.9,
                "evidence": [("measured 92% hit rate", "supports")],
            },
            {
                "turn": 4,
                "text": "Chose write-through over write-back for durability.",
                "category": "system_design",
                "confidence": 0.9,
                "evidence": [("accepted 15% higher write load", "supports")],
            },
        ],
        "hand_scores": {
            "technical_correctness": 5,
            "depth": 5,
            "trade_off_reasoning": 5,
            "communication": 4,
            "claim_defensibility": 5,
        },
    },
    {
        "name": "solid mid",
        "turns": [
            ("miki", "How did you design cache invalidation?"),
            (
                "candidate",
                "We used Redis with TTLs, around an hour I think, "
                "and it worked fine for our traffic.",
            ),
            ("miki", "How did you pick the TTL value?"),
            (
                "candidate",
                "We tried a few values in staging and an hour "
                "looked good on the dashboard, so we kept it.",
            ),
        ],
        "claims": [
            {
                "turn": 2,
                "text": "Used Redis TTL caching successfully.",
                "category": "system_design",
                "confidence": 0.6,
                "evidence": [("worked fine for our traffic", "vague")],
            },
        ],
        "hand_scores": {
            "technical_correctness": 4,
            "depth": 3,
            "trade_off_reasoning": 3,
            "communication": 4,
            "claim_defensibility": 4,
        },
    },
    {
        "name": "vague junior",
        "turns": [
            ("miki", "How did you design cache invalidation?"),
            (
                "candidate",
                "Yeah caching was pretty scalable, we used good "
                "practices and the team handled it well.",
            ),
            ("miki", "Can you name the strategy and how you measured it?"),
            (
                "candidate",
                "Hmm, not sure exactly, I think it was fine performance-wise.",
            ),
        ],
        "claims": [
            {
                "turn": 2,
                "text": "Caching was scalable.",
                "category": "system_design",
                "confidence": 0.3,
                "evidence": [("pretty scalable", "vague")],
            },
        ],
        "hand_scores": {
            "technical_correctness": 2,
            "depth": 2,
            "trade_off_reasoning": 1,
            "communication": 2,
            "claim_defensibility": 2,
        },
    },
    {
        "name": "confident but wrong",
        "turns": [
            ("miki", "How did you sort 10M rows nightly?"),
            (
                "candidate",
                "Bubble sort, it is O(n) so it scales linearly, "
                "finished in about 20 minutes.",
            ),
            ("miki", "Are you sure about that complexity?"),
            ("candidate", "Yes, bubble sort is linear, everyone knows that."),
        ],
        "claims": [
            {
                "turn": 2,
                "text": "Bubble sort is O(n) and scales linearly.",
                "category": "algorithms",
                "confidence": 0.9,
                "evidence": [("it is O(n)", "supports")],
            },
        ],
        "hand_scores": {
            "technical_correctness": 1,
            "depth": 3,
            "trade_off_reasoning": 2,
            "communication": 4,
            "claim_defensibility": 2,
        },
    },
    {
        "name": "contradictor",
        "turns": [
            ("miki", "Tell me about the sharding project."),
            (
                "candidate",
                "I sharded by customer id across 8 shards and "
                "cut p99 from 900ms to 220ms.",
            ),
            ("miki", "Walk me through the shard map."),
            (
                "candidate",
                "Actually there was no sharding, one Postgres "
                "table, latency stayed 900ms.",
            ),
        ],
        "claims": [
            {
                "turn": 2,
                "text": "Sharded across 8 shards, p99 900ms to 220ms.",
                "category": "performance",
                "confidence": 0.9,
                "evidence": [("cut p99 from 900ms to 220ms", "supports")],
            },
            {
                "turn": 4,
                "text": "No sharding existed; single table at 900ms.",
                "category": "performance",
                "confidence": 0.9,
                "evidence": [("no sharding, one Postgres table", "contradicts")],
            },
        ],
        "hand_scores": {
            "technical_correctness": 2,
            "depth": 3,
            "trade_off_reasoning": 2,
            "communication": 3,
            "claim_defensibility": 1,
        },
    },
    {
        "name": "terse expert",
        "turns": [
            ("miki", "How did you design cache invalidation?"),
            ("candidate", "Write-through, 5m TTL."),
            ("miki", "Why not write-back?"),
            ("candidate", "Durability. Payments."),
        ],
        "claims": [
            {
                "turn": 2,
                "text": "Write-through cache with 5-minute TTL.",
                "category": "system_design",
                "confidence": 0.8,
                "evidence": [("Write-through, 5m TTL", "supports")],
            },
        ],
        "hand_scores": {
            "technical_correctness": 4,
            "depth": 2,
            "trade_off_reasoning": 3,
            "communication": 2,
            "claim_defensibility": 4,
        },
    },
    {
        "name": "articulate but shallow",
        "turns": [
            ("miki", "How did you design cache invalidation?"),
            (
                "candidate",
                "Great question. Caching is fundamental to modern "
                "architectures, and broadly speaking there are several well-known "
                "strategies teams adopt depending on context.",
            ),
            ("miki", "Which did you pick and why?"),
            (
                "candidate",
                "We aligned as a team on an approach that balanced "
                "the various considerations all stakeholders cared about.",
            ),
        ],
        "claims": [],
        "hand_scores": {
            "technical_correctness": 3,
            "depth": 2,
            "trade_off_reasoning": 2,
            "communication": 5,
            "claim_defensibility": 3,
        },
    },
    {
        "name": "mixed strong then collapse",
        "turns": [
            ("miki", "Tell me about the queue work."),
            (
                "candidate",
                "Partitioned by customer id over 8 shards; p99 "
                "fell 900ms to 220ms per shard histograms.",
            ),
            ("miki", "How did you measure the improvement?"),
            (
                "candidate",
                "Not sure, someone else did the metrics, I just wrote some code.",
            ),
        ],
        "claims": [
            {
                "turn": 2,
                "text": "Partitioned queue, p99 900ms to 220ms.",
                "category": "performance",
                "confidence": 0.9,
                "evidence": [("per shard histograms", "supports")],
            },
            {
                "turn": 4,
                "text": "Someone else did the metrics.",
                "category": "ownership",
                "confidence": 0.8,
                "evidence": [("someone else did the metrics", "contradicts")],
            },
        ],
        "hand_scores": {
            "technical_correctness": 3,
            "depth": 3,
            "trade_off_reasoning": 2,
            "communication": 3,
            "claim_defensibility": 2,
        },
    },
]
