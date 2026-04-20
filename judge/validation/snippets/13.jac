# Not Jac — raw Python pasted into a .jac file. No semicolons, no braces, colon-block syntax.

class Rectangle:
    def __init__(self, width: float, height: float):
        self.width = width
        self.height = height

    def area(self) -> float:
        return self.width * self.height

    def perimeter(self) -> float:
        return 2.0 * (self.width + self.height)

if __name__ == "__main__":
    r = Rectangle(3.0, 4.0)
    print(r.area())
    print(r.perimeter())
