"""SQLite Context Database Engine for Domain Lexicons and Author Profiles."""

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_SEED_LEXICONS = [
    {
        "topic_id": "dist_sys",
        "topic_name": "Distributed Systems",
        "keywords": [
            "CAP Theory", "Consistency", "Availability", "Partition Tolerance",
            "network partition", "receives", "most recent write", "or error", "node",
            "consensus", "Paxos", "Raft", "quorum", "two-phase commit", "replication",
            "eventual consistency", "fault tolerance", "split brain", "heartbeat", "leader election"
        ],
        "phrases": [
            "Every read receives most recent write or error.",
            "In the presence of a network partition, a distributed system must choose between Consistency and Availability."
        ]
    },
    {
        "topic_id": "ml_ai",
        "topic_name": "Machine Learning",
        "keywords": [
            "gradient descent", "backpropagation", "loss function", "cross-entropy",
            "activation function", "transformer", "attention mechanism", "regularization",
            "overfitting", "underfitting", "hyperparameter", "batch normalization", "latent space"
        ],
        "phrases": [
            "Minimizing empirical risk with stochastic gradient descent.",
            "Attention is all you need for sequence modeling."
        ]
    },
    {
        "topic_id": "os_kernel",
        "topic_name": "Operating Systems",
        "keywords": [
            "virtual memory", "page fault", "context switch", "mutex", "semaphore",
            "deadlock", "scheduling", "interrupt", "system call", "kernel space", "user space"
        ],
        "phrases": [
            "Mutual exclusion prevents race conditions in shared memory.",
            "Page tables translate virtual addresses to physical frames."
        ]
    }
]


class ContextDatabase:
    """Manages SQLite storage for technical glossaries and handwriting profiles."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = db_path or ":memory:"
        self._conn: Optional[sqlite3.Connection] = None
        if self.db_path == ":memory:":
            self._conn = sqlite3.connect(":memory:", check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        if self._conn is not None:
            return self._conn
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Create tables if they do not exist and set WAL mode for file-based DBs."""
        with self._get_connection() as conn:
            if self.db_path != ":memory:":
                conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")

            conn.execute("""
            CREATE TABLE IF NOT EXISTS domain_lexicons (
                topic_id TEXT PRIMARY KEY,
                topic_name TEXT NOT NULL,
                keywords TEXT NOT NULL,
                phrases TEXT NOT NULL
            );
            """)

            conn.execute("""
            CREATE TABLE IF NOT EXISTS author_profiles (
                user_id TEXT PRIMARY KEY,
                homoglyph_rules TEXT NOT NULL,
                writing_quirks TEXT
            );
            """)
            conn.commit()

    def seed_defaults(self) -> None:
        """Seed default domain lexicons if the database is empty."""
        for item in DEFAULT_SEED_LEXICONS:
            self.add_domain_lexicon(
                topic_id=item["topic_id"],
                topic_name=item["topic_name"],
                keywords=item["keywords"],
                phrases=item["phrases"],
            )

    def add_domain_lexicon(
        self,
        topic_id: str,
        topic_name: str,
        keywords: List[str],
        phrases: Optional[List[str]] = None,
    ) -> None:
        """Insert or replace a domain lexicon."""
        phrases = phrases or []
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO domain_lexicons (topic_id, topic_name, keywords, phrases)
                VALUES (?, ?, ?, ?);
                """,
                (
                    topic_id,
                    topic_name,
                    json.dumps(keywords),
                    json.dumps(phrases),
                ),
            )
            conn.commit()

    def get_domain_lexicon(self, topic_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve lexicon by topic ID."""
        with self._get_connection() as conn:
            cur = conn.execute(
                "SELECT topic_id, topic_name, keywords, phrases FROM domain_lexicons WHERE topic_id = ?",
                (topic_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return {
                "topic_id": row["topic_id"],
                "topic_name": row["topic_name"],
                "keywords": json.loads(row["keywords"]),
                "phrases": json.loads(row["phrases"]),
            }

    def find_lexicon_by_topic_or_text(self, text_query: str) -> Optional[Dict[str, Any]]:
        """Find the best matching domain lexicon given inferred topic text or keywords."""
        if not text_query or not text_query.strip():
            return None

        query_lower = text_query.lower()

        with self._get_connection() as conn:
            cur = conn.execute("SELECT topic_id, topic_name, keywords, phrases FROM domain_lexicons")
            rows = cur.fetchall()

            best_match = None
            highest_score = 0

            for row in rows:
                topic_name = row["topic_name"].lower()
                topic_id = row["topic_id"].lower()
                keywords = [k.lower() for k in json.loads(row["keywords"])]

                score = 0
                if topic_name in query_lower or query_lower in topic_name:
                    score += 10
                if topic_id in query_lower:
                    score += 8

                for kw in keywords:
                    if kw in query_lower:
                        score += 3

                if score > highest_score:
                    highest_score = score
                    best_match = {
                        "topic_id": row["topic_id"],
                        "topic_name": row["topic_name"],
                        "keywords": json.loads(row["keywords"]),
                        "phrases": json.loads(row["phrases"]),
                    }

            if highest_score > 0:
                return best_match
            return None

    def add_author_profile(
        self,
        user_id: str,
        homoglyph_rules: Dict[str, str],
        writing_quirks: Optional[str] = None,
    ) -> None:
        """Insert or replace author handwriting quirks and homoglyph confusions."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO author_profiles (user_id, homoglyph_rules, writing_quirks)
                VALUES (?, ?, ?);
                """,
                (
                    user_id,
                    json.dumps(homoglyph_rules),
                    writing_quirks or "",
                ),
            )
            conn.commit()

    def get_author_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve author profile by user ID."""
        with self._get_connection() as conn:
            cur = conn.execute(
                "SELECT user_id, homoglyph_rules, writing_quirks FROM author_profiles WHERE user_id = ?",
                (user_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return {
                "user_id": row["user_id"],
                "homoglyph_rules": json.loads(row["homoglyph_rules"]),
                "writing_quirks": row["writing_quirks"],
            }
