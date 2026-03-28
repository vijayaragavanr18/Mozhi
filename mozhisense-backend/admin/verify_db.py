"""MozhiSense database auditing script.

Performs health checks on Words, Senses, and Challenges data to ensure
frontend-safe challenge rendering.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = BASE_DIR / "db" / "mozhisense.db"


class Color:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"


@dataclass
class Corruption:
    challenge_id: int
    reasons: list[str]


def hline(char: str = "=", width: int = 78) -> str:
    return char * width


def title(text: str) -> str:
    return f"{Color.BOLD}{Color.CYAN}{text}{Color.RESET}"


def status_ok(text: str) -> str:
    return f"{Color.GREEN}{text}{Color.RESET}"


def status_warn(text: str) -> str:
    return f"{Color.YELLOW}{text}{Color.RESET}"


def status_bad(text: str) -> str:
    return f"{Color.RED}{text}{Color.RESET}"


def get_connection(db_path: Path) -> sqlite3.Connection:
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND lower(name)=lower(?) LIMIT 1",
        (table_name,),
    ).fetchone()
    return row is not None


def fetch_macro_metrics(conn: sqlite3.Connection) -> dict[str, int]:
    metrics: dict[str, int] = {}
    for table in ("Words", "Senses", "Challenges"):
        if table_exists(conn, table):
            value = conn.execute(f"SELECT COUNT(*) AS c FROM {table}").fetchone()["c"]
            metrics[table] = int(value)
        else:
            metrics[table] = -1
    return metrics


def fetch_failed_words(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    if not table_exists(conn, "Words") or not table_exists(conn, "Challenges"):
        return []

    return conn.execute(
        """
        SELECT w.id, w.word_text
        FROM Words w
        LEFT JOIN Challenges c ON c.word_id = w.id
        GROUP BY w.id, w.word_text
        HAVING COUNT(c.id) = 0
        ORDER BY w.word_text
        """
    ).fetchall()


def fetch_failed_senses(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    if not table_exists(conn, "Senses") or not table_exists(conn, "Challenges"):
        return []

    return conn.execute(
        """
        SELECT s.id, w.word_text, s.meaning, s.pos
        FROM Senses s
        JOIN Words w ON w.id = s.word_id
        LEFT JOIN Challenges c ON c.sense_id = s.id
        GROUP BY s.id, w.word_text, s.meaning, s.pos
        HAVING COUNT(c.id) = 0
        ORDER BY w.word_text, s.id
        """
    ).fetchall()


def validate_challenges(conn: sqlite3.Connection) -> tuple[int, list[Corruption], list[int]]:
    if not table_exists(conn, "Challenges"):
        return 0, [Corruption(-1, ["Challenges table not found"])], []

    rows = conn.execute(
        "SELECT id, sentence_tamil, correct_answer, distractors_json FROM Challenges ORDER BY id"
    ).fetchall()

    total = len(rows)
    corruptions: list[Corruption] = []
    valid_ids: list[int] = []

    for row in rows:
        reasons: list[str] = []
        challenge_id = int(row["id"])

        sentence_tamil = str(row["sentence_tamil"] or "").strip()
        correct_answer = str(row["correct_answer"] or "").strip()
        distractors_blob = row["distractors_json"]

        parsed: Any = None
        try:
            parsed = json.loads(distractors_blob)
        except Exception:
            reasons.append("distractors_json is invalid JSON")

        if parsed is not None:
            if not isinstance(parsed, list):
                reasons.append("distractors_json is not a JSON list")
            elif len(parsed) != 3:
                reasons.append(f"distractors list length is {len(parsed)} (expected 3)")

        if "______" not in sentence_tamil:
            reasons.append("sentence_tamil missing blank token '______'")

        if not correct_answer:
            reasons.append("correct_answer is empty")

        if reasons:
            corruptions.append(Corruption(challenge_id, reasons))
        else:
            valid_ids.append(challenge_id)

    return total, corruptions, valid_ids


def fetch_random_valid_sample(conn: sqlite3.Connection) -> sqlite3.Row | None:
    if not all(table_exists(conn, t) for t in ("Words", "Senses", "Challenges")):
        return None

    return conn.execute(
        """
        SELECT
            c.id,
            w.word_text,
            s.meaning,
            s.english_translation,
            s.pos,
            c.sentence_tamil,
            c.correct_answer,
            c.distractors_json
        FROM Challenges c
        JOIN Words w ON w.id = c.word_id
        JOIN Senses s ON s.id = c.sense_id
        WHERE
            c.correct_answer IS NOT NULL
            AND TRIM(c.correct_answer) != ''
            AND c.sentence_tamil LIKE '%______%'
        ORDER BY RANDOM()
        LIMIT 1
        """
    ).fetchone()


def print_report(db_path: Path) -> int:
    print(hline())
    print(title("MozhiSense DB Health Report"))
    print(f"DB Path: {db_path}")
    print(hline())

    try:
        with get_connection(db_path) as conn:
            metrics = fetch_macro_metrics(conn)

            print(title("1) Macro Metrics"))
            for key in ("Words", "Senses", "Challenges"):
                value = metrics[key]
                if value >= 0:
                    print(f"  - {key:<11}: {status_ok(str(value))}")
                else:
                    print(f"  - {key:<11}: {status_bad('TABLE MISSING')}")
            print(hline("-"))

            print(title("2) Orphan Check (Missing Data)"))
            failed_words = fetch_failed_words(conn)
            failed_senses = fetch_failed_senses(conn)

            if failed_words:
                print(status_warn(f"  Failed Words ({len(failed_words)}):"))
                for row in failed_words:
                    print(f"    • [Word #{row['id']}] {row['word_text']}")
            else:
                print(status_ok("  No failed words. All words have at least one challenge."))

            if failed_senses:
                print(status_warn(f"  Failed Senses ({len(failed_senses)}):"))
                for row in failed_senses[:20]:
                    print(f"    • [Sense #{row['id']}] {row['word_text']} | {row['pos']} | {row['meaning']}")
                if len(failed_senses) > 20:
                    print(f"    ... and {len(failed_senses) - 20} more")
            else:
                print(status_ok("  No failed senses. All senses have at least one challenge."))
            print(hline("-"))

            print(title("3) Data Integrity Check"))
            total_rows, corruptions, valid_ids = validate_challenges(conn)
            print(f"  - Total challenge rows scanned : {total_rows}")
            print(f"  - Valid rows                   : {status_ok(str(len(valid_ids)))}")
            print(f"  - Corrupted rows               : {status_bad(str(len(corruptions))) if corruptions else status_ok('0')}")

            if corruptions:
                print(status_bad("  Corrupted Challenge IDs:"))
                for item in corruptions:
                    cid = item.challenge_id
                    if cid < 0:
                        print(f"    • [N/A] {', '.join(item.reasons)}")
                    else:
                        print(f"    • ID {cid}: {'; '.join(item.reasons)}")
            print(hline("-"))

            print(title("4) Quality Sample (Random Valid Challenge)"))
            sample = fetch_random_valid_sample(conn)
            if sample is None:
                print(status_warn("  No valid challenge sample found."))
            else:
                try:
                    distractors = json.loads(sample["distractors_json"])
                except Exception:
                    distractors = []

                print(f"  Challenge ID      : {sample['id']}")
                print(f"  Word              : {Color.BOLD}{sample['word_text']}{Color.RESET}")
                print(f"  Sense (TA)        : {sample['meaning']}")
                print(f"  Sense (EN)        : {sample['english_translation']}")
                print(f"  POS               : {sample['pos']}")
                print(f"  Sentence          : {sample['sentence_tamil']}")
                print(f"  Correct Answer    : {status_ok(sample['correct_answer'])}")
                print(f"  Distractors (3)   : {', '.join(distractors)}")

            print(hline())

            if corruptions:
                print(status_warn("Completed with warnings: corrupted rows detected."))
                return 1

            print(status_ok("Completed successfully: data looks frontend-safe."))
            return 0
    except Exception as exc:
        print(status_bad(f"Fatal error while auditing DB: {exc}"))
        return 2


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify MozhiSense SQLite DB integrity")
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB_PATH,
        help="Path to SQLite database file",
    )
    args = parser.parse_args()

    exit_code = print_report(args.db)
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
