import enum


class Previews(enum.Enum):
    """
    Enum class, assigning preview name with decode function.

    Usually used as e.g. :code:`Previews.color.name` when specifying color preview name.
    """

    COLOR = "color"
    LEFT = "left"
    RIGHT = "right"
