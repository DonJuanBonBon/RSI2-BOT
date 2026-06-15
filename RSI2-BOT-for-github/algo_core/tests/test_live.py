from algo_core.live import MockBroker, compute_orders, rebalance_to_targets


def test_buy_to_reach_target_from_flat():
    orders = compute_orders(equity=10_000.0, current_positions={},
                            target_weights={"A": 0.5}, prices={"A": 100.0}, band=0.0)
    assert len(orders) == 1
    o = orders[0]
    assert o["symbol"] == "A" and o["side"] == "buy"
    assert abs(o["qty"] - 50.0) < 1e-6          # 0.5 * 10000 / 100 = 50 shares


def test_band_suppresses_small_adjustments():
    # already ~50% in A, target 50% -> within band -> no order
    orders = compute_orders(equity=10_000.0, current_positions={"A": 50.0},
                            target_weights={"A": 0.5}, prices={"A": 100.0}, band=0.02)
    assert orders == []


def test_long_only_no_shorts():
    # negative target floored to 0; holding A -> sell to flat, never short
    orders = compute_orders(equity=10_000.0, current_positions={"A": 50.0},
                            target_weights={"A": -0.5}, prices={"A": 100.0}, band=0.0)
    assert len(orders) == 1 and orders[0]["side"] == "sell"
    assert abs(orders[0]["qty"] - 50.0) < 1e-6   # sells exactly its holding, no more


def test_max_order_notional_caps_size():
    orders = compute_orders(equity=100_000.0, current_positions={},
                            target_weights={"A": 1.0}, prices={"A": 100.0}, band=0.0,
                            max_order_notional=5_000.0)
    assert orders[0]["notional"] <= 5_000.0 + 1e-6
    assert abs(orders[0]["qty"] - 50.0) < 1e-6   # 5000/100


def test_dry_run_places_nothing():
    broker = MockBroker(10_000.0, prices={"A": 100.0})
    orders = rebalance_to_targets(broker, {"A": 0.5}, {"A": 100.0}, band=0.0, dry_run=True)
    assert orders                                 # a plan exists
    assert broker.submitted == []                 # but nothing was sent
    assert broker.get_positions() == {}


def test_execute_moves_positions_toward_target():
    broker = MockBroker(10_000.0, prices={"A": 100.0, "B": 50.0})
    rebalance_to_targets(broker, {"A": 0.4, "B": 0.2}, {"A": 100.0, "B": 50.0},
                         band=0.0, dry_run=False)
    eq = broker.get_equity()
    a_w = broker.get_positions().get("A", 0) * 100.0 / eq
    b_w = broker.get_positions().get("B", 0) * 50.0 / eq
    assert abs(a_w - 0.4) < 0.02
    assert abs(b_w - 0.2) < 0.02


def test_execute_then_flat_sells_out():
    broker = MockBroker(10_000.0, prices={"A": 100.0})
    rebalance_to_targets(broker, {"A": 0.5}, {"A": 100.0}, band=0.0, dry_run=False)
    assert broker.get_positions().get("A", 0) > 0
    rebalance_to_targets(broker, {}, {"A": 100.0}, band=0.0, dry_run=False)
    assert broker.get_positions().get("A", 0.0) == 0.0


def test_one_rejected_order_does_not_stop_the_rest():
    from algo_core.live import Broker
    class Flaky(Broker):
        def __init__(self):
            self.done = []; self.cancelled = False
        def get_equity(self): return 1000.0
        def get_positions(self): return {}
        def cancel_all_orders(self): self.cancelled = True
        def submit_order(self, symbol, qty, side):
            if symbol == "BBB": raise Exception("insufficient buying power")
            self.done.append(symbol)
    b = Flaky()
    prices = {"AAA": 100.0, "BBB": 100.0, "CCC": 100.0}
    rebalance_to_targets(b, {"AAA": 0.2, "BBB": 0.2, "CCC": 0.2}, prices, band=0.0, dry_run=False)
    assert b.cancelled is True
    assert b.done == ["AAA", "CCC"]
