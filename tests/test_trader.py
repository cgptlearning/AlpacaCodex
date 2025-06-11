import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config
from trader import Trader

class DummyClient:
    pass

def test_position_size_basic():
    trader = Trader(DummyClient())
    assert trader._position_size(20) == 50

def test_position_size_rounding_and_minimum():
    trader = Trader(DummyClient())
    assert trader._position_size(33) == 30
    assert trader._position_size(1500) == 1
