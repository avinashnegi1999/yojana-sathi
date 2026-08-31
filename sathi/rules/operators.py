"""The seven comparison operators a scheme file may use.

# ! Three-valued on purpose. Every operator returns True, False or None, where
# ! None means "cannot decide" — the worker did not answer, or the scheme file
# ! still carries a "TODO" where the threshold belongs. None is never coerced to
# ! False anywhere downstream: "we don't know" and "you don't qualify" are
# ! different things to say to someone deciding whether to lose a day's wages.
"""

from sathi.core.schemes import STUB


class OperatorError(Exception):
    """The comparison itself is impossible — wrong types, bad shape."""


def _is_stub(v: object) -> bool:
    """A stub anywhere in the expected value makes the whole comparison unknown."""
    if v == STUB:
        return True
    if isinstance(v, (list, tuple)):
        return any(_is_stub(x) for x in v)
    return False


def _num(v: object, where: str) -> float:
    # * bool is a subclass of int in Python. Comparing True to an age band is a
    # * scheme-file bug, so it is an error, not a silent 1.
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise OperatorError(f"{where}: expected a number, got {v!r}")
    return float(v)


def apply(op: str, actual: object, expected: object) -> bool | None:
    """Compare one profile value against one scheme threshold.

    Returns None when the answer is genuinely unknown. Raises OperatorError when
    the comparison is nonsense (a scheme-file bug the caller reports, never hides).
    """
    if op == "exists":
        # * The one operator that is decidable with no answer: absence IS the answer.
        return actual is not None

    if _is_stub(expected):
        return None
    if actual is None:
        return None

    if op == "between":
        if not isinstance(expected, (list, tuple)) or len(expected) != 2:
            raise OperatorError(f"'between' needs a [low, high] pair, got {expected!r}")
        lo, hi = _num(expected[0], "between.low"), _num(expected[1], "between.high")
        if lo > hi:
            raise OperatorError(f"'between' bounds are reversed: {expected!r}")
        # ! Inclusive at BOTH ends. Scheme texts usually read "18 to 40 years"
        # ! meaning 18 and 40 both qualify. A file where the boundary is
        # ! exclusive must encode that in the numbers, and say so in a comment.
        return lo <= _num(actual, "between.actual") <= hi

    if op in ("in", "not_in"):
        if not isinstance(expected, (list, tuple)):
            raise OperatorError(f"{op!r} needs a list, got {expected!r}")
        hit = actual in expected
        return hit if op == "in" else not hit

    if op == "lte":
        return _num(actual, "lte.actual") <= _num(expected, "lte.value")
    if op == "gte":
        return _num(actual, "gte.actual") >= _num(expected, "gte.value")

    if op == "eq":
        # * Exact match, no coercion. "yes" != True, 18 != "18".
        return actual == expected

    raise OperatorError(f"unknown operator {op!r}")


def _self_check() -> None:
    assert apply("between", 30, [18, 40]) is True
    assert apply("between", 18, [18, 40]) is True, "lower bound is inclusive"
    assert apply("between", 40, [18, 40]) is True, "upper bound is inclusive"
    assert apply("between", 41, [18, 40]) is False
    assert apply("between", None, [18, 40]) is None, "no answer is unknown, not a refusal"
    assert apply("between", 30, STUB) is None, "unresearched threshold is unknown"
    assert apply("between", 30, [STUB, 40]) is None, "half-researched is still unknown"

    assert apply("in", "upto_5000", ["upto_5000", "5001_10000"]) is True
    assert apply("in", "above_25000", ["upto_5000"]) is False
    assert apply("not_in", "above_25000", ["upto_5000"]) is True

    assert apply("lte", 3, 5) is True and apply("gte", 3, 5) is False
    assert apply("eq", True, True) is True and apply("eq", False, True) is False
    assert apply("eq", "18", 18) is False, "no type coercion"

    assert apply("exists", None, STUB) is False, "exists decides even with a stub"
    assert apply("exists", "construction", STUB) is True

    for bad in (
        ("between", 30, [40, 18]),
        ("between", "thirty", [18, 40]),
        ("in", "x", "not-a-list"),
        ("lte", True, 5),
        ("nonsense", 1, 1),
    ):
        try:
            apply(*bad)
        except OperatorError:
            pass
        else:
            raise AssertionError(f"{bad} should have raised OperatorError")
    print("operators.py OK")


if __name__ == "__main__":
    _self_check()
