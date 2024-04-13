import time
import sys

def Fibonacci(n):
    """Calculates the nth Fibonacci number recursively.

    Args:
        n (int): The index of the Fibonacci number to calculate.

    Returns:
        int: The nth Fibonacci number.

    Raises:
        ValueError: If n is negative.
    """

    if n < 0:
        raise ValueError("Incorrect input: n must be non-negative")

    if n == 0:
        return 0

    if n == 1 or n == 2:
        return 1

    return Fibonacci(n-1) + Fibonacci(n-2)


def main():
    """Driver program to calculate the Fibonacci number using command-line arguments.

    Usage: python fibonacci.py <n>

    where <n> is the non-negative integer for which you want to calculate the Fibonacci number.
    """

    if len(sys.argv) != 2:
        print("Usage: python fibonacci.py <n>")
        sys.exit(1)

    try:
        n = int(sys.argv[1])
        if n < 0:
            raise ValueError
    except ValueError:
        print("Incorrect input: n must be a non-negative integer")
        sys.exit(1)

    start_time = time.time()
    result = Fibonacci(n)
    end_time = time.time()

    print(f"Fibonacci of {n} is: {result}")
    print(f"Calculated in: {end_time - start_time:.8f} seconds")


if __name__ == "__main__":
    main()