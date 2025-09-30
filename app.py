import tkinter as tk
from tkinter import simpledialog, colorchooser, messagebox
from shape import RectangleShape, CircleShape, TriangleShape, ShapeGroup
from visitor import AreaCalculatorVisitor
from PIL import Image, ImageDraw, ImageFont


class SpacePlannerApp:
    def __init__(self, root, room_width, room_height):
        self.root = root
        self.room_width = room_width
        self.room_height = room_height
        self.root.title("Space Planner")
        self.room_area = self.room_width * self.room_height

        # Cadre à gauche pour les boutons et détails
        self.control_frame = tk.Frame(self.root, bg="#f5f5f5")
        self.control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        # Canvas à droite
        self.canvas = tk.Canvas(self.root, width=room_width, height=room_height, bg="#f0e6d6")
        self.canvas.pack(side=tk.RIGHT, padx=5, pady=5)

        self.shape_group = ShapeGroup()
        self.selected_shape = None
        self.drag_offset_x = 0
        self.drag_offset_y = 0

        self.current_shape_type = tk.StringVar(value="rectangle")

        # Valeur par défaut de l'angle de rotation
        self.rotation_angle = tk.IntVar(value=15)

        self.setup_controls()
        self.bind_events()

    def _styled_button(self, parent, text, command):
        """
        Crée un bouton stylisé : fond bleu, texte blanc, arrondi léger.
        """
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            font=("Helvetica", 10, "bold"),
            bg="#3B75AF",
            fg="white",
            activebackground="#315f8e",
            activeforeground="white",
            bd=0,
            relief="raised",
            padx=10,
            pady=5,
        )
        btn.pack(fill=tk.X, pady=4)
        return btn

    def _styled_radiobutton(self, parent, text, value):
        """
        Crée un Radiobutton stylisé (plein, sans cercle).
        """
        rb = tk.Radiobutton(
            parent,
            text=text,
            variable=self.current_shape_type,
            value=value,
            font=("Helvetica", 10),
            bg="#f5f5f5",
            fg="#333333",
            activeforeground="#333333",
            activebackground="#f5f5f5",
            selectcolor="#d1e4ff",
            indicatoron=0,  # bouton plein
            width=12,
            relief="ridge",
            bd=1,
            pady=4
        )
        rb.pack(anchor=tk.W, pady=2)
        return rb

    def setup_controls(self):
        # Titre
        title_lbl = tk.Label(
            self.control_frame,
            text="Outils",
            font=("Helvetica", 12, "bold"),
            bg="#f5f5f5",
            fg="#3B75AF"
        )
        title_lbl.pack(pady=(0, 10))

        # Radiobuttons
        self._styled_radiobutton(self.control_frame, "Rectangle", "rectangle")
        self._styled_radiobutton(self.control_frame, "Circle", "circle")
        self._styled_radiobutton(self.control_frame, "Triangle", "triangle")

        # Boutons d'action
        self._styled_button(self.control_frame, "Add Shape", self.add_shape)
        self._styled_button(self.control_frame, "Delete Shape", self.delete_shape)

        rotate_btn = self._styled_button(self.control_frame, "Rotate Shape", self.rotate_shape)

        # Champ pour entrer l'angle de rotation, juste en dessous du bouton
        angle_frame = tk.Frame(self.control_frame, bg="#f5f5f5")
        angle_frame.pack(fill=tk.X, pady=(0, 10))
        angle_lbl = tk.Label(
            angle_frame,
            text="Angle (°) :",
            font=("Helvetica", 10),
            bg="#f5f5f5",
            fg="#333333"
        )
        angle_lbl.pack(side=tk.LEFT, padx=(2, 5))
        angle_entry = tk.Entry(
            angle_frame,
            textvariable=self.rotation_angle,
            font=("Helvetica", 10),
            width=5,
            bd=1,
            relief="solid",
            justify="center"
        )
        angle_entry.pack(side=tk.LEFT)

        self._styled_button(self.control_frame, "Détails", self.calculate_area)
        self._styled_button(self.control_frame, "Save as PNG", lambda: self.export_canvas_to_png())

        # Étiquette d'aire totale
        self.area_label = tk.Label(
            self.control_frame,
            text=f"Room Area = {self.room_area:.2f}\nUsed: 0\nRemaining: {self.room_area:.2f}",
            font=("Helvetica", 10),
            bg="#f5f5f5",
            fg="#333333",
            wraplength=140,
            justify=tk.LEFT
        )
        self.area_label.pack(fill=tk.X, pady=(10, 0))

        # Séparateur
        sep = tk.Frame(self.control_frame, height=1, bg="#cccccc")
        sep.pack(fill=tk.X, pady=10)

        # Titre détails forme
        details_title = tk.Label(
            self.control_frame,
            text="Détails forme",
            font=("Helvetica", 11, "bold"),
            bg="#f5f5f5",
            fg="#3B75AF"
        )
        details_title.pack(pady=(0, 5))

        # Label pour afficher les détails de la forme sélectionnée
        self.detail_label = tk.Label(
            self.control_frame,
            text="Aucune forme sélectionnée",
            font=("Helvetica", 10),
            bg="#f5f5f5",
            fg="#333333",
            wraplength=140,
            justify=tk.LEFT
        )
        self.detail_label.pack(fill=tk.X, pady=(0, 5))

    def bind_events(self):
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)

    def on_click(self, event):
        """
        Sélectionne la forme cliquée, affiche ses détails,
        ou désélectionne si clic en dehors.
        """
        for shape in reversed(self.shape_group.children):
            if shape.contains(event.x, event.y):
                self.selected_shape = shape
                self.drag_offset_x = event.x - shape.x
                self.drag_offset_y = event.y - shape.y
                self.show_shape_details(shape)
                return

        # Clic en dehors de toute forme
        self.selected_shape = None
        self.detail_label.config(text="Aucune forme sélectionnée")

    def on_drag(self, event):
        if self.selected_shape:
            new_x = event.x - self.drag_offset_x
            new_y = event.y - self.drag_offset_y

            moved = self.selected_shape.move_to(
                new_x, new_y, self.room_width, self.room_height, self.shape_group.children
            )
            if moved:
                self.redraw()

    def redraw(self):
        self.canvas.delete("all")
        self.shape_group.draw(self.canvas)

        visitor = AreaCalculatorVisitor()
        self.shape_group.accept(visitor)
        total = visitor.get_total_area()
        remaining = self.room_width * self.room_height - total
        self.area_label.config(
            text=f"Room Area = {self.room_area:.2f}\nUsed: {total:.2f}\nRemaining: {remaining:.2f}"
        )

    def add_shape(self):
        name = simpledialog.askstring("Shape Name", "Enter name :")
        if name is None:
            return
        color = colorchooser.askcolor()[1]
        if color is None:
            return

        shape = None
        shape_area = 0

        if self.current_shape_type.get() == "rectangle":
            w = simpledialog.askinteger("Width", "Enter width :")
            h = simpledialog.askinteger("Height", "Enter height :")
            if w is None or h is None:
                return
            shape = RectangleShape(name, 0, 0, w, h, color, angle=0)
            shape_area = w * h

        elif self.current_shape_type.get() == "circle":
            r = simpledialog.askinteger("Radius", "Enter radius :")
            if r is None:
                return
            shape = CircleShape(name, 0, 0, r, color)
            shape_area = 3.14 * r * r

        else:  # triangle
            b = simpledialog.askinteger("Base", "Enter base length :")
            h = simpledialog.askinteger("Height", "Enter height :")
            if b is None or h is None:
                return
            shape = TriangleShape(name, 0, 0, b, h, color, angle=0)
            shape_area = (b * h) / 2

        visitor = AreaCalculatorVisitor()
        self.shape_group.accept(visitor)
        if visitor.get_total_area() + shape_area > self.room_width * self.room_height:
            messagebox.showerror("Surface limit exceeded", "Not enough space in the room. Please remove a shape.")
            return

        spawn = self.find_spawn_position(shape)
        if spawn is None:
            messagebox.showerror("Aucun emplacement libre", "Impossible de placer la forme : plus d'espace disponible.")
            return

        shape.x, shape.y = spawn

        if isinstance(shape, RectangleShape):
            if shape.x + shape.width > self.room_width or shape.y + shape.height > self.room_height:
                messagebox.showerror("Trop grand", "Ce rectangle ne rentre pas dans la pièce.")
                return
        elif isinstance(shape, CircleShape):
            if shape.x < 0 or shape.y < 0 or shape.x + 2 * shape.radius > self.room_width or shape.y + 2 * shape.radius > self.room_height:
                messagebox.showerror("Trop grand", "Ce cercle ne rentre pas dans la pièce.")
                return
        else:  # TriangleShape
            verts = shape.get_vertices()
            xs = [px for (px, _) in verts]
            ys = [py for (_, py) in verts]
            if min(xs) < 0 or min(ys) < 0 or max(xs) > self.room_width or max(ys) > self.room_height:
                messagebox.showerror("Trop grand", "Ce triangle ne rentre pas dans la pièce.")
                return

        self.shape_group.add(shape)
        self.redraw()

    def delete_shape(self):
        if self.selected_shape:
            self.shape_group.remove(self.selected_shape)
            self.selected_shape = None
            self.detail_label.config(text="Aucune forme sélectionnée")
            self.redraw()

    def rotate_shape(self):
        """
        Lit l'angle depuis self.rotation_angle (Entry).
        Applique à la forme sélectionnée si possible.
        """
        if self.selected_shape is None:
            messagebox.showwarning("Sélectionnez une forme", "Aucune forme sélectionnée à faire pivoter.")
            return

        if not isinstance(self.selected_shape, (RectangleShape, TriangleShape)):
            messagebox.showinfo("Rotation impossible", "Seuls les rectangles et triangles peuvent être tournés.")
            return

        try:
            angle = self.rotation_angle.get()
        except tk.TclError:
            messagebox.showerror("Valeur invalide", "Veuillez entrer un nombre entier pour l'angle.")
            return

        shape = self.selected_shape
        old_angle = shape.angle
        shape.angle = (shape.angle + angle) % 360

        can_rotate = shape.move_to(
            shape.x, shape.y, self.room_width, self.room_height, self.shape_group.children
        )
        if not can_rotate:
            shape.angle = old_angle
            messagebox.showerror(
                "Rotation impossible",
                "La forme ne peut pas être tournée ici (collision ou hors pièce)."
            )
            return

        self.redraw()
        self.show_shape_details(shape)

    def calculate_area(self):
        visitor = AreaCalculatorVisitor()
        self.shape_group.accept(visitor)
        total = visitor.get_total_area()
        details = visitor.get_details()
        remaining = self.room_width * self.room_height - total

        report = f"Room area: {self.room_width * self.room_height:.2f} units²\n\n"
        report += "Shapes:\n"
        for name, area in details:
            report += f" - {name}: {area:.2f} units²\n"
        report += f"\nUsed area: {total:.2f} units²\n"
        report += f"Remaining area: {remaining:.2f} units²"

        messagebox.showinfo("Area Details", report)
        self.redraw()

    def export_canvas_to_png(self, filename="room.png"):
        img = Image.new("RGB", (self.room_width, self.room_height), "#f0e6d6")
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", 14)
        except:
            font = ImageFont.load_default()

        for shape in self.shape_group.children:
            if isinstance(shape, RectangleShape):
                corners = shape.get_corners()
                coords = []
                for (px, py) in corners:
                    coords.extend([px, py])
                draw.polygon(coords, fill=shape.color, outline="black")
                cx, cy = shape.get_center()
                draw.text((cx, cy), shape.name, fill="black", font=font, anchor="mm")

            elif isinstance(shape, CircleShape):
                r = shape.radius
                draw.ellipse(
                    [shape.x, shape.y, shape.x + 2 * r, shape.y + 2 * r],
                    fill=shape.color
                )
                draw.text((shape.x + r, shape.y + r), shape.name, fill="black", font=font, anchor="mm")

            elif isinstance(shape, TriangleShape):
                verts = shape.get_vertices()
                coords = []
                for (px, py) in verts:
                    coords.extend([px, py])
                draw.polygon(coords, fill=shape.color, outline="black")
                cx, cy = shape.get_center()
                draw.text((cx, cy), shape.name, fill="black", font=font, anchor="mm")

        img.save(filename)

    def find_spawn_position(self, shape):
        pas = 1

        if isinstance(shape, RectangleShape):
            base_w, base_h = shape.width, shape.height
            base_angle = shape.angle
            max_x_possible = self.room_width - base_w
            max_y_possible = self.room_height - base_h
            if max_x_possible < 0 or max_y_possible < 0:
                return None

        elif isinstance(shape, CircleShape):
            base_r = shape.radius
            max_x_possible = self.room_width - 2 * base_r
            max_y_possible = self.room_height - 2 * base_r
            if max_x_possible < 0 or max_y_possible < 0:
                return None

        else:  # TriangleShape
            base_b, base_h = shape.base, shape.height
            base_angle = shape.angle
            max_x_possible = self.room_width
            max_y_possible = self.room_height

        for y in range(0, max_y_possible + 1, pas):
            for x in range(0, max_x_possible + 1, pas):
                if isinstance(shape, RectangleShape):
                    temp = RectangleShape(
                        name=shape.name + "_tmp",
                        x=x, y=y,
                        width=base_w, height=base_h,
                        color=shape.color,
                        angle=base_angle
                    )
                    corners = temp.get_corners()
                    xs = [px for (px, _) in corners]
                    ys = [py for (_, py) in corners]
                    if min(xs) < 0 or min(ys) < 0 or max(xs) > self.room_width or max(ys) > self.room_height:
                        continue

                elif isinstance(shape, CircleShape):
                    temp = CircleShape(
                        name=shape.name + "_tmp",
                        x=x, y=y,
                        radius=base_r,
                        color=shape.color
                    )
                    if x < 0 or y < 0 or x + 2 * base_r > self.room_width or y + 2 * base_r > self.room_height:
                        continue

                else:  # TriangleShape
                    temp = TriangleShape(
                        name=shape.name + "_tmp",
                        x=x, y=y,
                        base=shape.base,
                        height=shape.height,
                        color=shape.color,
                        angle=shape.angle
                    )
                    verts = temp.get_vertices()
                    xs = [px for (px, _) in verts]
                    ys = [py for (_, py) in verts]
                    if min(xs) < 0 or min(ys) < 0 or max(xs) > self.room_width or max(ys) > self.room_height:
                        continue

                collision = False
                for existing in self.shape_group.children:
                    if temp.intersects_with(existing) or existing.intersects_with(temp):
                        collision = True
                        break

                if not collision:
                    return (x, y)

        return None

    def show_shape_details(self, shape):
        """
        Remplit la zone de détail avec : nom, type, dimensions, angle, aire.
        """
        if isinstance(shape, RectangleShape):
            stype = "Rectangle"
            dims = f"Width={shape.width}, Height={shape.height}"
            angle = shape.angle
            area = shape.width * shape.height

        elif isinstance(shape, CircleShape):
            stype = "Circle"
            dims = f"Radius={shape.radius}"
            angle = "N/A"
            area = 3.1416 * shape.radius ** 2

        else:  # TriangleShape
            stype = "Triangle"
            dims = f"Base={shape.base}, Height={shape.height}"
            angle = shape.angle
            area = (shape.base * shape.height) / 2

        detail_text = (
            f"Name: {shape.name}\n"
            f"Type: {stype}\n"
            f"{dims}\n"
            f"Angle: {angle}°\n"
            f"Area: {area:.2f}"
        )
        self.detail_label.config(text=detail_text)


