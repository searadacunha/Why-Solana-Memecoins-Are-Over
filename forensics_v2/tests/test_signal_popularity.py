from forensics_v2.investigations.signal_popularity import mint_band, perimeter_signal_only, t200_band


def test_bands_of_t200():
    assert t200_band(200, "max_pages", 30) == "a_1m"
    assert t200_band(200, "max_pages", 599) == "b_10m"
    assert t200_band(200, "max_pages", 3599) == "c_1h"
    assert t200_band(200, "max_pages", 3600) == "d_more"
    assert t200_band(120, "genesis", 90000) == "under_200"
    assert t200_band(120, "max_pages", 10) is None  # a short read that did not end says nothing
    assert t200_band(200, "max_pages", None) is None


def test_mint_band_uses_creation_as_the_start():
    assert mint_band({"t_create": 100, "last_t": 150, "n_tx": 200, "stop": "max_pages"}) == "a_1m"
    assert mint_band({"t_create": None, "last_t": 150, "n_tx": 200, "stop": "max_pages"}) is None


def test_signal_from_the_perimeter_only():
    side = {"S1": True, "buyers_checked": [{"s1": True, "buyer": "a"}, {"s1": False, "buyer": "z"}]}
    assert perimeter_signal_only(side, {"a"})
    assert not perimeter_signal_only(side, {"b"})
    assert not perimeter_signal_only({"S1": False, "buyers_checked": []}, {"a"})
