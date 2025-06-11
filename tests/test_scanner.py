import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config
from datamanager import DataManager, AssetInfo
from scanner import Scanner


def _scanner():
    dm = DataManager()
    return Scanner(dm, lambda s, p: None)


def test_meets_criteria_all_false_cases():
    scanner = _scanner()
    symbol = "TEST"
    info = AssetInfo(symbol=symbol, prev_close=10.0, avg_volume=1000)

    # Price outside min/max
    scanner.hod[symbol] = 10.5
    scanner.volume[symbol] = 6000
    assert not scanner._meets_criteria(symbol, 1.0, info)

    # Price below required pct change
    scanner.hod[symbol] = 11.0
    scanner.volume[symbol] = 6000
    assert not scanner._meets_criteria(symbol, 10.5, info)

    # Insufficient volume
    scanner.hod[symbol] = 11.0
    scanner.volume[symbol] = 4000
    assert not scanner._meets_criteria(symbol, 11.0, info)

    # Missing HOD
    scanner.hod[symbol] = 0.0
    scanner.volume[symbol] = 6000
    assert not scanner._meets_criteria(symbol, 11.0, info)

    # Price too far from HOD
    scanner.hod[symbol] = 11.0
    scanner.volume[symbol] = 6000
    far_price = 11.0 * (1 - config.HOD_PROXIMITY_PCT - 0.01)
    assert not scanner._meets_criteria(symbol, far_price, info)


def test_meets_criteria_success():
    scanner = _scanner()
    symbol = "TEST"
    info = AssetInfo(symbol=symbol, prev_close=10.0, avg_volume=1000)
    scanner.hod[symbol] = 11.0
    scanner.volume[symbol] = 6000
    price = 11.0
    assert scanner._meets_criteria(symbol, price, info)
