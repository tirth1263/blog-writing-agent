from agents import GeneratedArticle, StyleProfile
from memory import MemoryStore, article_to_html


def profile():
    return StyleProfile(
        tone="Warm",
        voice="Direct",
        structure="Scannable",
        vocabulary="Accessible",
        sentence_patterns="Balanced",
        examples_style="Concrete",
        signature_traits=["Reader-first"],
        source_word_count=500,
    )


def test_profile_and_article_roundtrip(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    saved = profile()
    store.save_profile("writer-1", saved)
    assert store.latest_profile("writer-1").tone == "Warm"

    article = GeneratedArticle("A title", "# A title\n\nUseful content.", "Useful content.", 3, "test")
    article_id = store.save_article("writer-1", article)
    rows = store.list_articles("writer-1")
    assert rows[0]["title"] == "A title"
    assert store.delete_article("writer-1", article_id)
    assert store.list_articles("writer-1") == []


def test_html_export_escapes_content():
    article = GeneratedArticle(
        "Safe <title>",
        "# Safe <title>\n\n<script>alert(1)</script>\n\n1. **First** step",
        "excerpt",
        4,
        "test",
    )
    exported = article_to_html(article)
    assert "<script>alert" not in exported
    assert "&lt;script&gt;" in exported
    assert "<strong>First</strong>" in exported
