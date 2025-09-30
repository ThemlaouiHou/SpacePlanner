from math import pi

class ShapeVisitor:
    def visit_rectangle(self, rectangle):
        pass

    def visit_circle(self, circle):
        pass

    def visit_triangle(self, triangle):
        pass


class AreaCalculatorVisitor(ShapeVisitor):
    def __init__(self):
        self.total_area = 0
        self.details = []

    def visit_rectangle(self, rectangle):
        area = rectangle.width * rectangle.height
        self.total_area += area
        self.details.append((rectangle.name, area))

    def visit_circle(self, circle):
        area = pi * circle.radius**2
        self.total_area += area
        self.details.append((circle.name, area))

    def visit_triangle(self, triangle):
        area = (triangle.base * triangle.height) / 2
        self.total_area += area
        self.details.append((triangle.name, area))

    def get_total_area(self):
        return self.total_area

    def get_details(self):
        return self.details
