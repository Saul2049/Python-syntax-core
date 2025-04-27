from src import broker

def test_position_size():
    assert broker.compute_position_size(100_000, 500) == 4  # 2% risk

def test_stop_price():
    assert broker.compute_stop_price(100, 5) == 95 