"""lib_verif: the backward pagination that dates a wallet's first signature,
and the two small statistics the v0* scripts report next to it.

first_signature is the one that can lie by omission: it walks pages backwards
under a cap, and what it returns has to say whether it reached the beginning or
merely ran out of budget. v08_ages.py filters its population on that flag.
"""
import lib_verif


def _pages(monkeypatch, pages):
    """Serve `pages` in order to each get_sigs call, then empty pages."""
    calls = []

    def fake(addr, limit=1000, before=None):
        calls.append(before)
        return pages[len(calls) - 1] if len(calls) <= len(pages) else []

    monkeypatch.setattr(lib_verif, "get_sigs", fake)
    return calls


def _sig(name, ts):
    return {"signature": name, "blockTime": ts}


def test_a_short_page_means_the_beginning_was_reached(monkeypatch):
    full = [_sig("s%d" % i, 1000 + i) for i in range(1000)]
    tail = [_sig("older1", 5), _sig("older2", 4)]
    _pages(monkeypatch, [full, tail])
    sig, ts, pages, censored = lib_verif.first_signature("A")
    assert (sig, ts) == ("older2", 4)
    assert pages == 2
    assert censored is False


def test_a_single_short_page_needs_no_second_call(monkeypatch):
    calls = _pages(monkeypatch, [[_sig("only", 7)]])
    sig, ts, pages, censored = lib_verif.first_signature("A")
    assert (sig, ts, pages, censored) == ("only", 7, 1, False)
    assert calls == [None], "la premiere page se demande sans curseur"


def test_pagination_walks_backwards_from_the_last_signature(monkeypatch):
    full = [_sig("s%d" % i, i) for i in range(1000)]
    calls = _pages(monkeypatch, [full, [_sig("end", 0)]])
    lib_verif.first_signature("A")
    assert calls == [None, "s999"], "la page suivante part de la derniere signature vue"


def test_hitting_the_cap_is_reported_as_censored(monkeypatch):
    """40 full pages and still no end: the birth date returned is a lower
    bound, not the birth date, and the flag is what says so."""
    full = [_sig("s%d" % i, i) for i in range(1000)]
    _pages(monkeypatch, [full] * 40)
    sig, ts, pages, censored = lib_verif.first_signature("A")
    assert pages == 40
    assert censored is True


def test_an_address_with_no_signature_returns_nothing(monkeypatch):
    """Nothing found: the caller gets None rather than a fabricated date.

    Note the flag comes back True here, which reads as 'truncated' although the
    walk simply found an empty history. v08_ages.py is unaffected because it
    also requires first_ts, which is None in this case.
    """
    _pages(monkeypatch, [[]])
    sig, ts, pages, censored = lib_verif.first_signature("A")
    assert sig is None and ts is None
    assert pages == 1


# ------------------------------------------------------------------ stats ---
def test_cv_is_zero_below_two_points_and_on_a_zero_mean():
    assert lib_verif.cv([]) == 0.0
    assert lib_verif.cv([5.0]) == 0.0
    assert lib_verif.cv([-1.0, 1.0]) == 0.0, "moyenne nulle: pas de division"


def test_cv_is_the_population_dispersion_over_the_mean():
    # pstdev([2, 4]) = 1, mean = 3
    assert lib_verif.cv([2.0, 4.0]) == 1 / 3
    assert lib_verif.cv([5.0, 5.0, 5.0]) == 0.0