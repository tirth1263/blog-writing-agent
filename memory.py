"""Privacy-first persistence for style profiles and generated articles."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from agents import GeneratedArticle, StyleProfile


class MemoryStore:
    """Small SQLite repository that complements Memori's conversation memory.

    Memori captures and recalls LLM interactions. This store keeps app-specific
    artifacts available even in local/demo mode, and does not store source files.
    """

    def __init__(self, database_path: str | Path = ".data/blog_agent.db") -> None:
        self.path = Path(database_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS style_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    profile_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_style_profiles_user
                    ON style_profiles(user_id, id DESC);

                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    excerpt TEXT NOT NULL,
                    content TEXT NOT NULL,
                    word_count INTEGER NOT NULL,
                    mode TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_articles_user
                    ON articles(user_id, id DESC);
                """
            )

    def save_profile(self, user_id: str, profile: StyleProfile) -> int:
        with self._connect() as connection:
            cursor = connection.execute(
                "INSERT INTO style_profiles (user_id, profile_json, created_at) VALUES (?, ?, ?)",
                (user_id, json.dumps(profile.to_dict()), profile.analyzed_at),
            )
            return int(cursor.lastrowid)

    def latest_profile(self, user_id: str) -> StyleProfile | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT profile_json FROM style_profiles WHERE user_id = ? ORDER BY id DESC LIMIT 1",
                (user_id,),
            ).fetchone()
        return StyleProfile.from_dict(json.loads(row["profile_json"])) if row else None

    def save_article(self, user_id: str, article: GeneratedArticle) -> int:
        with self._connect() as connection:
            cursor = connection.execute(
                """INSERT INTO articles
                   (user_id, title, excerpt, content, word_count, mode, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    user_id,
                    article.title,
                    article.excerpt,
                    article.content,
                    article.word_count,
                    article.mode,
                    article.created_at,
                ),
            )
            return int(cursor.lastrowid)

    def list_articles(self, user_id: str, limit: int = 20) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """SELECT id, title, excerpt, content, word_count, mode, created_at
                   FROM articles WHERE user_id = ? ORDER BY id DESC LIMIT ?""",
                (user_id, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def delete_article(self, user_id: str, article_id: int) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM articles WHERE id = ? AND user_id = ?",
                (article_id, user_id),
            )
            return cursor.rowcount > 0


def article_to_html(article: GeneratedArticle) -> str:
    """Return a self-contained, escaped HTML export."""
    import html
    import re

    lines: list[str] = []
    in_list = False
    for raw in article.content.splitlines():
        line = raw.strip()
        if not line:
            if in_list:
                lines.append("</ol>")
                in_list = False
            continue
        if line.startswith("# "):
            lines.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.startswith("## "):
            if in_list:
                lines.append("</ol>")
                in_list = False
            lines.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif re.match(r"^\d+\.\s", line):
            if not in_list:
                lines.append("<ol>")
                in_list = True
            item = re.sub(r"^\d+\.\s*", "", line)
            item = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html.escape(item))
            lines.append(f"<li>{item}</li>")
        elif line.startswith("> "):
            lines.append(f"<blockquote>{html.escape(line[2:])}</blockquote>")
        else:
            body = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html.escape(line))
            lines.append(f"<p>{body}</p>")
    if in_list:
        lines.append("</ol>")
    body = "\n".join(lines)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>{html.escape(article.title)}</title>
<style>body{{font:18px/1.7 Georgia,serif;max-width:760px;margin:64px auto;padding:0 24px;color:#17231d}}
h1,h2{{font-family:Arial,sans-serif;line-height:1.15}}h1{{font-size:2.8rem}}h2{{margin-top:2.2rem}}
blockquote{{border-left:4px solid #b8ef63;margin-left:0;padding-left:1rem;color:#526158}}</style></head>
<body>{body}</body></html>"""
