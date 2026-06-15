import pytest
from algo_core.live.alpaca_broker import AlpacaBroker

def test_requires_credentials(monkeypatch):
    monkeypatch.delenv("ALPACA_API_KEY", raising=False)
    monkeypatch.delenv("ALPACA_SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError, match="ALPACA_API_KEY"):
        AlpacaBroker(paper=True)

def test_refuses_live_without_override(monkeypatch):
    monkeypatch.setenv("ALPACA_API_KEY", "fake")
    monkeypatch.setenv("ALPACA_SECRET_KEY", "fake")
    monkeypatch.delenv("ALPACA_ALLOW_LIVE", raising=False)
    with pytest.raises(RuntimeError, match="Refusing LIVE"):
        AlpacaBroker(paper=False, allow_live=True)

def test_paper_requires_alpaca_installed(monkeypatch):
    monkeypatch.setenv("ALPACA_API_KEY", "fake")
    monkeypatch.setenv("ALPACA_SECRET_KEY", "fake")
    try:
        import alpaca  # noqa: F401
        pytest.skip("alpaca-py installed; guard path not exercised")
    except ImportError:
        pass
    with pytest.raises(RuntimeError, match="alpaca-py not installed"):
        AlpacaBroker(paper=True)
