"""Fibonacci: returns the n-th Fibonacci number (fib(0)=0, fib(1)=1)."""

def fib(n: int) -> int {
    if n <= 1 {
        return n;
    }
    return fib(n - 1) + fib(n - 2);
}
