"""Tests for the pilot fibonacci task."""

import from solution { fib }

test "fib base case 0" {
    assert fib(0) == 0;
}

test "fib base case 1" {
    assert fib(1) == 1;
}

test "fib n=10" {
    assert fib(10) == 55;
}
