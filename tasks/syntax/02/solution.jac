"""Rectangle archetype with area and perimeter methods."""

obj Rectangle {
    has width: float;
    has height: float;

    def area() -> float {
        return self.width * self.height;
    }

    def perimeter() -> float {
        return 2.0 * (self.width + self.height);
    }
}
