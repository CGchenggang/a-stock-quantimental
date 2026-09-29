import json

from astock_v2.cli import main


def test_cli_research_uses_provider_boundary(monkeypatch, capsys):
    class FakeProvider:
        name = "fake"

        def quote(self, symbols):
            from astock_v2.data.providers import ProviderResult
            return ProviderResult(
                data={"quotes": {"000001": {"price": 10.2}}},
                source="fake_quote",
                source_type="test",
                fetched_at="2026-09-27T00:00:00+00:00",
                available_time="2026-09-27T00:00:00+00:00",
            )

        def daily(self, symbol, start, end):
            from astock_v2.data.providers import ProviderResult
            return ProviderResult(
                data={"latest_date": "2026-09-26", "latest": {"close": 10.0}},
                source="fake_daily",
                source_type="test",
                fetched_at="2026-09-27T00:00:00+00:00",
                available_time="2026-09-27T00:00:00+00:00",
            )

        def index_daily(self, symbol):
            from astock_v2.data.providers import ProviderResult
            return ProviderResult(
                data={"latest_date": "2026-09-26", "pct": 1.2, "ma20": 3950.0, "above_ma20": True},
                source="fake_index",
                source_type="test",
                fetched_at="2026-09-27T00:00:00+00:00",
                available_time="2026-09-27T00:00:00+00:00",
            )

        def sector_board(self):
            from astock_v2.data.providers import ProviderResult
            return ProviderResult(
                data={"sectors": [{"name": "A", "pct": 1.0}, {"name": "B", "pct": -1.0}]},
                source="fake_sector",
                source_type="test",
                fetched_at="2026-09-27T00:00:00+00:00",
                available_time="2026-09-27T00:00:00+00:00",
            )

        def market_turnover(self):
            from astock_v2.data.providers import ProviderResult
            return ProviderResult(
                data={"turnover_z": None, "pit_ready": False, "amount": 100.0},
                source="fake_turnover",
                source_type="test",
                fetched_at="2026-09-27T00:00:00+00:00",
                available_time="2026-09-27T00:00:00+00:00",
            )

    monkeypatch.setattr(
        "astock_v2.cli.build_legacy_market_provider",
        lambda: FakeProvider(),
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "astock-v2",
            "research",
            "000001",
            "--decision-time",
            "2026-09-27T08:00:00+08:00",
            "--daily-start",
            "2026-09-20",
            "--daily-end",
            "2026-09-26",
        ],
    )
    main()
    result = json.loads(capsys.readouterr().out)
    assert result["symbol"] == "000001"
    assert result["market"]["quotes"]["000001"]["price"] == 10.2
    assert result["stock"]["daily"]["latest"]["close"] == 10.0
    assert result["model"] == {}
    assert result["risk"]["flags"] == ["QUANT_MODEL_NOT_RUN"]
    assert result["data_quality"]["availability_complete"] is True
