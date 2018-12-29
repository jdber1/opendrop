class IFTPhysicalParameters:
    def __init__(self, inner_density: float, outer_density: float, needle_width: float, gravity: float) -> None:
        self.inner_density = inner_density
        self.outer_density = outer_density
        self.needle_width = needle_width
        self.gravity = gravity
