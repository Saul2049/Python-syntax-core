# is_prime.py
# -----------------------------------------------------------
# Purpose : Return True if n is a prime number, else False.
# Author  : So (learning Python fundamentals)
# -----------------------------------------------------------

from math import isqrt


def is_prime(n: int) -> bool:
    """
    Check whether `n` is a prime number.

    Parameters
    ----------
    n : int
        The integer we want to test for primality.

    Returns
    -------
    bool
        True  → n is prime
        False → n is composite or < 2
    """
    # handle small and even/3 divisibility edge-cases
    if n < 2:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    # test divisors of form 6k±1 up to integer square root
    limit = isqrt(n)
    for i in range(5, limit + 1, 6):
        if n % i == 0 or n % (i + 2) == 0:
            return False
    return True  # no divisors found ⇒ n is prime


# Quick manual check (runs when you press ▶ in Cursor)
if __name__ == "__main__":
    print(is_prime(11))  # expect True
    print(is_prime(12))  # expect False
