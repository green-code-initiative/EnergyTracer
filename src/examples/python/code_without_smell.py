TIMEOUT = 10


def compute():
    total = 0
    for i in range(1_000_000):
        total += TIMEOUT * i
    return total


compute()
