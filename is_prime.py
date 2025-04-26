# is_prime.py
# -----------------------------------------------------------
# Purpose : Return True if n is a prime number, else False.
# Author  : So (learning Python fundamentals)
# -----------------------------------------------------------

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
    if n < 2:                     # 0 and 1 are not prime by definition
        return False

    # Only test divisors up to √n, because if n = a·b,
    # one factor must be ≤ the square root of n.
    for p in range(2, int(n**0.5) + 1):  # iterate over potential divisors
        if n % p == 0:            # remainder 0 ⇒ p divides n ⇒ not prime
            return False

    return True                   # no divisors found ⇒ n is prime


# Quick manual check (runs when you press ▶ in Cursor)
if __name__ == "__main__":
    print(is_prime(11))  # expect True
    print(is_prime(12))  # expect False
