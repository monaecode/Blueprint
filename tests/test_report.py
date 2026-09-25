"""Tests for report rendering (HTML always; PDF when a backend is installed)."""

import pytest

from pentest_agent import analysis as analysis_mod
from pentest_agent import report as report_mod

jinja2 = pytest.importorskip("jinja2", reason="jinja2 not installed")


def _sample_context():
    scope = {
        "engagement": {"client": "TestCo", "engagement_id": "T-1",
                       "start_date": "2026-09-19", "end_date": "2026-09-19"},
        "targets": [{"host": "127.0.0.1", "ports": [3000]}],
        "intensity": "standard",
        "authorization": {"signed_by": "Tester"},
    }
    raw = {"http://127.0.0.1:3000": [{
        "template-id": "ssl-test",
        "info": {"name": "TLS Issue", "severity": "high",
                 "description": "Weak TLS."},
        "matched-at": "http://127.0.0.1:3000",
    }]}
    analyzed = analysis_mod.analyze(raw)
    recon = {"127.0.0.1": {"subdomains": [], "ports": {3000: {
        "service": "http", "product": "Node", "version": "20"}}, "tech": {}}}
    return report_mod.build_context(scope, recon, analyzed,
                                    audit_entries=[{"ts": "t", "cmd": ["nmap"],
                                                   "returncode": 0, "note": ""}],
                                    template_categories=["ssl-test"])


def test_build_context_sections():
    ctx = _sample_context()
    assert ctx["client"] == "TestCo"
    assert ctx["summary"]["High"] == 1
    assert "immediate attention" not in ctx["executive_summary"]  # high, not critical
    assert "prompt remediation" in ctx["executive_summary"]


def test_render_html_contains_sections(tmp_path):
    ctx = _sample_context()
    html = report_mod.render_html(ctx, tmp_path / "r.html")
    text = html.read_text()
    for section in ["Executive Summary", "Methodology", "Findings",
                    "Appendix A", "TLS Issue"]:
        assert section in text


def test_generate_report_pdf_if_backend(tmp_path):
    try:
        import reportlab  # noqa: F401
        has_backend = True
    except ImportError:
        try:
            import weasyprint  # noqa: F401
            has_backend = True
        except ImportError:
            has_backend = False
    if not has_backend:
        pytest.skip("no PDF backend installed (reportlab or weasyprint)")
    ctx = _sample_context()
    out = report_mod.generate_report(ctx, tmp_path)
    assert out.suffix == ".pdf" and out.stat().st_size > 0
