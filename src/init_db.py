import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "finsight.db"


def main():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        connection.executescript("""
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY,
                exchange TEXT NOT NULL,
                symbol TEXT NOT NULL,
                company_name TEXT NOT NULL,
                official_website TEXT,
                registry_source_url TEXT,
                registry_checked_at TEXT,
                UNIQUE(exchange, symbol)
            );

            CREATE TABLE IF NOT EXISTS company_logos (
                company_id INTEGER PRIMARY KEY,
                source_url TEXT,
                local_path TEXT,
                status TEXT NOT NULL DEFAULT 'pending'
                    CHECK (
                        status IN (
                            'pending', 'downloaded', 'reviewed',
                            'not_found', 'failed'
                        )
                    ),
                manual_override INTEGER NOT NULL DEFAULT 0
                    CHECK (manual_override IN (0, 1)),
                checked_at TEXT,
                last_error TEXT,
                FOREIGN KEY(company_id)
                    REFERENCES companies(id)
            );

            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY,
                company_id INTEGER NOT NULL,
                report_type TEXT NOT NULL,
                period_end TEXT NOT NULL,
                source_url TEXT,
                local_path TEXT NOT NULL,
                sha256 TEXT NOT NULL,
                downloaded_at TEXT,
                extraction_status TEXT NOT NULL DEFAULT 'pending'
                    CHECK (
                        extraction_status IN (
                            'pending', 'extracted',
                            'needs_review', 'failed'
                        )
                    ),
                UNIQUE(company_id, sha256),
                FOREIGN KEY(company_id)
                    REFERENCES companies(id)
            );
        """)

        tables = connection.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            ORDER BY name
        """).fetchall()

    print(f"Database ready: {DB_PATH}")
    print("Tables:", ", ".join(row[0] for row in tables))


if __name__ == "__main__":
    main()