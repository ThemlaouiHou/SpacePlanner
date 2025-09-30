from abc import ABC, abstractmethod
import math


class Shape(ABC):
    def __init__(self, name, color):
        self.name = name
        self.color = color

    @abstractmethod
    def draw(self, canvas):
        pass

    @abstractmethod
    def contains(self, x, y):
        pass

    @abstractmethod
    def move_to(self, x, y, max_width, max_height, all_shapes):
        pass

    @abstractmethod
    def accept(self, visitor):
        pass

    @abstractmethod
    def intersects_with(self, other):
        pass


class RectangleShape(Shape):
    def __init__(self, name, x, y, width, height, color, angle=0):
        super().__init__(name, color)
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.angle = angle  # en degrés

    def get_center(self):
        cx = self.x + self.width / 2
        cy = self.y + self.height / 2
        return cx, cy

    def get_corners(self):
        cx, cy = self.get_center()
        θ = math.radians(self.angle)
        cos_t = math.cos(θ)
        sin_t = math.sin(θ)

        pts = [
            (self.x, self.y),
            (self.x + self.width, self.y),
            (self.x + self.width, self.y + self.height),
            (self.x, self.y + self.height),
        ]

        rotated = []
        for (px, py) in pts:
            dx = px - cx
            dy = py - cy
            qx = dx * cos_t - dy * sin_t + cx
            qy = dx * sin_t + dy * cos_t + cy
            rotated.append((qx, qy))

        return rotated

    def draw(self, canvas):
        corners = self.get_corners()
        coords = []
        for (px, py) in corners:
            coords.extend([px, py])
        self.id = canvas.create_polygon(coords, fill=self.color, outline="black")
        cx, cy = self.get_center()
        self.label_id = canvas.create_text(cx, cy, text=self.name)

    def contains(self, x, y):
        corners = self.get_corners()

        def area_sign(x1, y1, x2, y2, x3, y3):
            return (x2 - x1)*(y3 - y1) - (y2 - y1)*(x3 - x1)

        s0 = area_sign(corners[0][0], corners[0][1], corners[1][0], corners[1][1], x, y)
        s1 = area_sign(corners[1][0], corners[1][1], corners[2][0], corners[2][1], x, y)
        s2 = area_sign(corners[2][0], corners[2][1], corners[3][0], corners[3][1], x, y)
        s3 = area_sign(corners[3][0], corners[3][1], corners[0][0], corners[0][1], x, y)

        return (s0 >= 0 and s1 >= 0 and s2 >= 0 and s3 >= 0) or (s0 <= 0 and s1 <= 0 and s2 <= 0 and s3 <= 0)

    def move_to(self, x, y, max_width, max_height, all_shapes):
        old_x, old_y = self.x, self.y
        self.x, self.y = x, y

        corners = self.get_corners()
        xs = [px for (px, _) in corners]
        ys = [py for (_, py) in corners]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        if min_x < 0 or min_y < 0 or max_x > max_width or max_y > max_height:
            self.x, self.y = old_x, old_y
            return False

        for other in all_shapes:
            if other is self:
                continue
            if self.intersects_with(other):
                self.x, self.y = old_x, old_y
                return False

        return True

    def accept(self, visitor):
        visitor.visit_rectangle(self)

    def _project_onto_axis(self, corners, axis):
        projections = []
        ax, ay = axis
        for (px, py) in corners:
            projections.append(px * ax + py * ay)
        return min(projections), max(projections)

    def _axes_for_SAT(self, corners):
        axes = []
        for i in range(4):
            x1, y1 = corners[i]
            x2, y2 = corners[(i + 1) % 4]
            dx = x2 - x1
            dy = y2 - y1
            nx = -dy
            ny = dx
            length = math.hypot(nx, ny)
            if length != 0:
                axes.append((nx / length, ny / length))
        return axes

    def intersects_with(self, other):
        if isinstance(other, RectangleShape):
            corners1 = self.get_corners()
            corners2 = other.get_corners()

            axes1 = self._axes_for_SAT(corners1)
            axes2 = other._axes_for_SAT(corners2)
            axes = axes1[:2] + axes2[:2]

            for axis in axes:
                min1, max1 = self._project_onto_axis(corners1, axis)
                min2, max2 = self._project_onto_axis(corners2, axis)
                if max1 < min2 or max2 < min1:
                    return False
            return True

        if isinstance(other, CircleShape):
            cx = other.x + other.radius
            cy = other.y + other.radius
            r = other.radius
            if self.contains(cx, cy):
                return True

            corners = self.get_corners()
            for i in range(4):
                x1, y1 = corners[i]
                x2, y2 = corners[(i + 1) % 4]
                dx = x2 - x1
                dy = y2 - y1
                length_sq = dx * dx + dy * dy
                if length_sq == 0:
                    continue
                t = ((cx - x1) * dx + (cy - y1) * dy) / length_sq
                t = max(0, min(1, t))
                proj_x = x1 + t * dx
                proj_y = y1 + t * dy
                dist_sq = (cx - proj_x)**2 + (cy - proj_y)**2
                if dist_sq <= r * r:
                    return True

            for (px, py) in corners:
                d_sq = (cx - px)**2 + (cy - py)**2
                if d_sq <= r * r:
                    return True

            return False

        if isinstance(other, TriangleShape):
            verts1 = self.get_corners()
            verts2 = other.get_vertices()

            axes1 = self._axes_for_SAT(verts1)
            axes2 = other._axes_for_SAT(verts2)
            axes = axes1[:2] + axes2

            for axis in axes:
                min1, max1 = self._project_onto_axis(verts1, axis)
                min2, max2 = other._project_onto_axis(verts2, axis)
                if max1 < min2 or max2 < min1:
                    return False
            return True

        return False


class CircleShape(Shape):
    def __init__(self, name, x, y, radius, color):
        super().__init__(name, color)
        self.x, self.y = x, y
        self.radius = radius

    def draw(self, canvas):
        self.id = canvas.create_oval(
            self.x, self.y,
            self.x + 2 * self.radius, self.y + 2 * self.radius,
            fill=self.color
        )
        self.label_id = canvas.create_text(
            self.x + self.radius, self.y + self.radius,
            text=self.name
        )

    def contains(self, x, y):
        cx, cy = self.x + self.radius, self.y + self.radius
        return (x - cx)**2 + (y - cy)**2 <= self.radius**2

    def move_to(self, x, y, max_width, max_height, all_shapes):
        if x < 0 or y < 0 or (x + 2 * self.radius) > max_width or (y + 2 * self.radius) > max_height:
            return False

        old_x, old_y = self.x, self.y
        self.x, self.y = x, y

        for shape in all_shapes:
            if shape is not self and self.intersects_with(shape):
                self.x, self.y = old_x, old_y
                return False
        return True

    def accept(self, visitor):
        visitor.visit_circle(self)

    def intersects_with(self, other):
        if isinstance(other, CircleShape):
            cx1 = self.x + self.radius
            cy1 = self.y + self.radius
            cx2 = other.x + other.radius
            cy2 = other.y + other.radius
            dx = cx1 - cx2
            dy = cy1 - cy2
            dist_sq = dx * dx + dy * dy
            return dist_sq <= (self.radius + other.radius)**2

        if isinstance(other, RectangleShape) or isinstance(other, TriangleShape):
            return other.intersects_with(self)

        return False


class TriangleShape(Shape):
    def __init__(self, name, x, y, base, height, color, angle=0):
        super().__init__(name, color)
        self.x = x
        self.y = y
        self.base = base
        self.height = height
        self.angle = angle  # en degrés

    def get_center(self):
        cx = self.x + (self.base / 2)
        cy = self.y + (self.height * 2/3)
        return cx, cy

    def get_vertices(self):
        A = (self.x, self.y + self.height)
        B = (self.x + self.base / 2, self.y)
        C = (self.x + self.base, self.y + self.height)
        cx, cy = self.get_center()
        θ = math.radians(self.angle)
        cos_t = math.cos(θ)
        sin_t = math.sin(θ)

        def rotate_point(px, py):
            dx = px - cx
            dy = py - cy
            qx = dx * cos_t - dy * sin_t + cx
            qy = dx * sin_t + dy * cos_t + cy
            return (qx, qy)

        return [rotate_point(*A), rotate_point(*B), rotate_point(*C)]

    def draw(self, canvas):
        verts = self.get_vertices()
        coords = []
        for (px, py) in verts:
            coords.extend([px, py])
        self.id = canvas.create_polygon(coords, fill=self.color, outline="black")
        cx, cy = self.get_center()
        self.label_id = canvas.create_text(cx, cy, text=self.name)

    def contains(self, x, y):
        verts = self.get_vertices()
        (x1, y1), (x2, y2), (x3, y3) = verts

        def area(xa, ya, xb, yb, xc, yc):
            return abs((xa*(yb-yc) + xb*(yc-ya) + xc*(ya-yb))) / 2

        A_tot = area(x1, y1, x2, y2, x3, y3)
        A1 = area(x, y, x2, y2, x3, y3)
        A2 = area(x1, y1, x, y, x3, y3)
        A3 = area(x1, y1, x2, y2, x, y)

        return abs((A1 + A2 + A3) - A_tot) < 1e-6

    def move_to(self, x, y, max_width, max_height, all_shapes):
        old_x, old_y = self.x, self.y
        self.x, self.y = x, y

        verts = self.get_vertices()
        xs = [px for (px, _) in verts]
        ys = [py for (_, py) in verts]
        if min(xs) < 0 or min(ys) < 0 or max(xs) > max_width or max(ys) > max_height:
            self.x, self.y = old_x, old_y
            return False

        for other in all_shapes:
            if other is self:
                continue
            if self.intersects_with(other):
                self.x, self.y = old_x, old_y
                return False

        return True

    def accept(self, visitor):
        visitor.visit_triangle(self)

    def _project_onto_axis(self, verts, axis):
        projections = []
        ax, ay = axis
        for (px, py) in verts:
            projections.append(px * ax + py * ay)
        return min(projections), max(projections)

    def _axes_for_SAT(self, verts):
        axes = []
        for i in range(3):
            x1, y1 = verts[i]
            x2, y2 = verts[(i + 1) % 3]
            dx = x2 - x1
            dy = y2 - y1
            nx = -dy
            ny = dx
            length = math.hypot(nx, ny)
            if length != 0:
                axes.append((nx / length, ny / length))
        return axes

    def intersects_with(self, other):
        verts1 = self.get_vertices()

        if isinstance(other, TriangleShape):
            verts2 = other.get_vertices()
            axes1 = self._axes_for_SAT(verts1)
            axes2 = other._axes_for_SAT(verts2)
            axes = axes1 + axes2
            for axis in axes:
                min1, max1 = self._project_onto_axis(verts1, axis)
                min2, max2 = other._project_onto_axis(verts2, axis)
                if max1 < min2 or max2 < min1:
                    return False
            return True

        if isinstance(other, RectangleShape):
            verts2 = other.get_corners()
            axes1 = self._axes_for_SAT(verts1)
            axes2 = other._axes_for_SAT(verts2)
            axes = axes1 + axes2
            for axis in axes:
                min1, max1 = self._project_onto_axis(verts1, axis)
                min2, max2 = other._project_onto_axis(verts2, axis)
                if max1 < min2 or max2 < min1:
                    return False
            return True

        if isinstance(other, CircleShape):
            cx = other.x + other.radius
            cy = other.y + other.radius
            r = other.radius

            if self.contains(cx, cy):
                return True

            for i in range(3):
                x1, y1 = verts1[i]
                x2, y2 = verts1[(i + 1) % 3]
                dx = x2 - x1
                dy = y2 - y1
                length_sq = dx * dx + dy * dy
                if length_sq == 0:
                    continue
                t = ((cx - x1) * dx + (cy - y1) * dy) / length_sq
                t = max(0, min(1, t))
                proj_x = x1 + t * dx
                proj_y = y1 + t * dy
                dist_sq = (cx - proj_x)**2 + (cy - proj_y)**2
                if dist_sq <= r * r:
                    return True

            for (px, py) in verts1:
                d_sq = (cx - px)**2 + (cy - py)**2
                if d_sq <= r * r:
                    return True

            return False

        return False


class ShapeGroup(Shape):
    def __init__(self):
        super().__init__("Group", "white")
        self.children = []

    def add(self, shape):
        self.children.append(shape)

    def remove(self, shape):
        self.children.remove(shape)

    def draw(self, canvas):
        for shape in self.children:
            shape.draw(canvas)

    def contains(self, x, y):
        return any(shape.contains(x, y) for shape in self.children)

    def move_to(self, x, y, max_width, max_height, all_shapes):
        pass

    def accept(self, visitor):
        for shape in self.children:
            shape.accept(visitor)

    def intersects_with(self, other):
        return False
