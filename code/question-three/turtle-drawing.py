import turtle
import math

def koch_edge(t, length, depth):
    """
    Recursively draws a single edge of the Koch pattern.

    Args:
        t (turtle.Turtle): The turtle object used for drawing.
        length (float): The length of the current edge segment.
        depth (int): The current recursion depth.
    """
    if depth == 0:
        t.forward(length)
    else:
        short_length = length / 3.0
        koch_edge(t, short_length, depth - 1)
        t.left(60)
        koch_edge(t, short_length, depth - 1)
        t.right(120)
        koch_edge(t, short_length, depth - 1)
        t.left(60)
        koch_edge(t, short_length, depth - 1)

def draw_polygon(t, num_sides, side_length, depth):
    """
    Draws a regular polygon where each side is replaced by a Koch curve.

    Args:
        t (turtle.Turtle): The turtle object.
        num_sides (int): Number of sides of the initial polygon.
        side_length (float): Length of each side.
        depth (int): Recursion depth.
    """
    if num_sides < 3:
        print("A polygon must have at least 3 sides. Drawing nothing.")
        return

    angle = 360.0 / num_sides

    # Calculating the radius of the circumcircle
    radius = side_length / (2 * math.sin(math.pi / num_sides))

    # Screen dimensions (matching setworldcoordinates)
    screen_width = 800
    screen_height = 600
    center_x = screen_width / 2
    center_y = screen_height / 2

    # Adjusting to move the pattern up/down
    vertical_offset_multiplier = 2.5

    # Calculating the starting point based on the first vertex
    start_angle_rad = math.pi + (math.pi / num_sides) # Starting from bottom-left vertex
    start_x = center_x + radius * math.cos(start_angle_rad)
    start_y = center_y + radius * math.sin(start_angle_rad) + (radius * (vertical_offset_multiplier - 1))

    t.penup()
    t.goto(start_x, start_y)
    t.pendown()

    # Drawing each side of the polygon
    for _ in range(num_sides):
        koch_edge(t, side_length, depth)
        t.right(angle) # Turning to the next side


def main():
    """
    Main function to get user input and draw the recursive geometric pattern.
    """
    try:
        num_sides = int(input("Enter the number of sides: "))
        if num_sides < 3:
            raise ValueError("Number of sides must be at least 3.")
    except ValueError as e:
        print(f"Invalid input for number of sides: {e}")
        return

    try:
        side_length = float(input("Enter the side length: "))
        if side_length <= 0:
            raise ValueError("Side length must be positive.")
    except ValueError as e:
        print(f"Invalid input for side length: {e}")
        return

    try:
        depth = int(input("Enter the recursion depth: "))
        if depth < 0:
            raise ValueError("Recursion depth must be non-negative.")
    except ValueError as e:
        print(f"Invalid input for recursion depth: {e}")
        return

    # Setting up the screen
    screen = turtle.Screen()
    screen.title(f"Recursive Geometric Pattern (Sides: {num_sides}, Depth: {depth})")
    screen.bgcolor("white")
    screen.setup(width=800, height=600)
    screen.setworldcoordinates(0, 0, 800, 600)  # Fixed coordinate system

    t = turtle.Turtle()
    t.speed(0)
    t.pensize(1)
    t.color("black")

    # Drawing the pattern
    print("Drawing the pattern...")
    draw_polygon(t, num_sides, side_length, depth)
    print("Drawing complete. Click to close.")

    screen.exitonclick()


if __name__ == "__main__":
    main()