"""Golden / determinism tests."""

import numpy as np
from lfs.core.preset import example_local_first_signal
from lfs.dsp.engine import render
from lfs.semantic.classifier import classify
from lfs.semantic.prompt_compiler import compile_prompt, prompt_to_text


def test_render_determinism():
    p = example_local_first_signal()
    a = render(p, length_sec=2.0)
    b = render(p, length_sec=2.0)
    np.testing.assert_allclose(a, b, rtol=1e-5, atol=1e-6)


def test_different_seed_changes_audio():
    p1 = example_local_first_signal()
    p2 = example_local_first_signal()
    p2.seed = 999
    a = render(p1, length_sec=1.0)
    b = render(p2, length_sec=1.0)
    # Should not be identical
    assert not np.allclose(a, b, atol=1e-4)


def test_prompt_determinism():
    p = example_local_first_signal()
    profile = classify(p)
    s1 = compile_prompt(profile)
    s2 = compile_prompt(profile)
    assert prompt_to_text(s1) == prompt_to_text(s2)
    assert "Offline, offline" in (s1.lyrics or "")