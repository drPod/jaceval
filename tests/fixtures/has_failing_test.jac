obj Adder {
    has a: int;
    has b: int;

    def sum() -> int {
        return self.a + self.b;
    }
}

test "addition is wrong on purpose" {
    adder = Adder(a=2, b=3);
    assert adder.sum() == 999, "Expected intentional failure";
}
