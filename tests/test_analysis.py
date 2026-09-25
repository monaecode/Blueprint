"""Tests for finding normalization, dedupe, severity, and FP filtering."""

from pentest_agent.analysis import (
    analyze,
    dedupe,
    filter_false_positives,
    normalize,
    sort_by_severity,
    summarize,
)


def _raw(url="http://127.0.0.1:3000", template="ssl-test", severity="high",
         name="TLS Issue"):
    return {url: [{
        "template-id": template,
        "info": {"name": name, "severity": severity,
                 "description": "desc"},
        "matched-at": url,
    }]}


def test_normalize_maps_fields():
    findings = normalize(_raw())
    assert len(findings) == 1
    f = findings[0]
    assert f.host == "127.0.0.1" and f.port == 3000
    assert f.severity == "High"
    assert "nuclei template" in f.rationale
    assert f.remediation  # every finding gets remediation guidance


def test_dedupe_merges_evidence():
    raw = _raw()
    url = "http://127.0.0.1:3000"
    raw[url].append({"template-id": "ssl-test",
                     "info": {"name": "TLS Issue", "severity": "high"},
                     "matched-at": url + "/other"})
    findings = dedupe(normalize(raw))
    assert len(findings) == 1
    assert "/other" in findings[0].evidence


def test_filter_false_positives_logged():
    findings = normalize(_raw(template="tech-detect", name="Tech Detect",
                              severity="info"))
    kept, filtered = filter_false_positives(findings)
    assert kept == [] and len(filtered) == 1
    assert filtered[0].filter_reason  # reason recorded, not silently dropped


def test_sort_by_severity():
    findings = (normalize(_raw(template="a", severity="low"))
                + normalize(_raw(template="b", severity="critical")))
    ordered = sort_by_severity(findings)
    assert ordered[0].severity == "Critical"


def test_summarize_counts():
    findings = (normalize(_raw(template="a", severity="critical"))
                + normalize(_raw(template="b", severity="low")))
    s = summarize(findings)
    assert s["Critical"] == 1 and s["Low"] == 1 and s["Total"] == 2


def test_analyze_end_to_end():
    result = analyze(_raw())
    assert result["summary"]["Total"] == 1
    assert result["raw_count"] == 1
    assert isinstance(result["findings"], list)
