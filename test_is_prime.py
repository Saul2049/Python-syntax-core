from is_prime import is_prime

def test_small_primes():
    assert is_prime(2) is True
    assert is_prime(17) is True

def test_non_primes():
    assert is_prime(1) is False
    assert is_prime(20) is False
