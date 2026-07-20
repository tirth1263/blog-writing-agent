import io

import pytest

from agents import (
    ContentGenerator,
    DigitalOceanAgent,
    DocumentProcessor,
    GenerationRequest,
    ProcessedDocument,
    StyleAnalyzer,
)

SAMPLE = """
Good writing starts with a useful question. What does the reader need right now?

We can make complicated ideas feel simple without making them simplistic. For example,
imagine explaining a new workflow to a teammate on their first day. You would begin with
the reason it matters, show one concrete step, and give them room to try it.

That is the rhythm I return to: context, action, reflection. It keeps the work practical,
and it keeps the reader moving. The goal is not to sound clever. The goal is to be useful.
"""


def test_text_document_processing():
    document = DocumentProcessor().process(io.BytesIO(SAMPLE.encode()), name="sample.txt")
    assert document.file_type == "TXT"
    assert document.word_count > 50
    assert "useful question" in document.text


def test_unsupported_document_is_rejected():
    with pytest.raises(ValueError, match="Unsupported"):
        DocumentProcessor().process(io.BytesIO(b"content"), name="sample.csv")


def test_local_style_analysis_returns_complete_profile():
    document = ProcessedDocument("sample.txt", SAMPLE * 3, "TXT", 210, len(SAMPLE) * 3)
    profile = StyleAnalyzer().analyze([document])
    assert profile.analysis_mode == "Local linguistic analysis"
    assert profile.source_word_count > 150
    assert profile.average_sentence_length > 0
    assert len(profile.signature_traits) >= 2
    assert profile.tone and profile.voice and profile.structure


def test_demo_generation_is_publishable_markdown():
    request = GenerationRequest(
        topic="ethical AI in healthcare",
        audience="healthcare leaders",
        keywords=["patient trust", "governance"],
    )
    article = ContentGenerator().generate(request, None)
    assert article.content.startswith("# ")
    assert article.content.count("## ") >= 5
    assert "patient trust" in article.content
    assert article.word_count > 350
    assert article.mode == "Local demo engine"


def test_digitalocean_endpoint_normalization():
    agent = DigitalOceanAgent(None, None)
    assert not agent.configured
    agent.endpoint = "https://example.agents.do-ai.run"
    assert agent.base_url == "https://example.agents.do-ai.run/api/v1/"
    agent.endpoint = "https://example.agents.do-ai.run/api/v1"
    assert agent.base_url == "https://example.agents.do-ai.run/api/v1/"
