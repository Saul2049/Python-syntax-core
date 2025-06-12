import pytest

# 使用新 fixtures (fresh_collector) 来进行参数化测试

TRADE_CASES = [
    ("BTCUSDT", "buy", 50_000, 0.1),
    ("BTCUSDT", "sell", 51_000, 0.05),
    ("ETHUSDT", "buy", 3_000, 1.0),
]


@pytest.mark.parametrize("symbol,action,price,qty", TRADE_CASES)
def test_record_trade_and_summary(fresh_collector, symbol, action, price, qty):
    c = fresh_collector
    c.record_trade(symbol, action, price, qty)
    summary = c.get_trade_summary()
    assert summary[symbol][action] >= 1


@pytest.mark.parametrize(
    "module,msg",
    [
        ("api", "rate limit"),
        ("ws", "connection lost"),
        ("core", Exception("boom")),
    ],
)
def test_record_error_and_summary(fresh_collector, module, msg):
    fresh_collector.record_error(module, msg)
    es = fresh_collector.get_error_summary()
    assert es[module] == 1


def test_update_price_and_get_prices(fresh_collector):
    fresh_collector.update_price("BTCUSDT", 50_000)
    prices = fresh_collector.get_latest_prices()
    assert prices["BTCUSDT"] == 50_000


def test_reset_counters(fresh_collector):
    # populate some state
    fresh_collector.record_trade("BTCUSDT", "buy", 50_000, 0.1)
    fresh_collector.record_error("api", "oops")
    fresh_collector.reset_counters()
    assert fresh_collector.get_trade_summary() == {}
    assert fresh_collector.get_error_summary() == {}
