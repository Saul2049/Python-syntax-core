import pytest

from is_prime import is_prime


@pytest.mark.parametrize(
    "n, expected",
    [
        (-5, False),  # negative number edge-case
        (0, False),  # zero edge-case
        (2, True),  # small prime
        (17, True),  # medium prime
        (97, True),  # big prime edge-case
    ],
)
def test_edge_cases(n, expected):
    assert is_prime(n) is expected


@pytest.mark.parametrize("n", [1, 20, 100])  # composite values including larger
def test_non_primes(n):
    assert is_prime(n) is False
