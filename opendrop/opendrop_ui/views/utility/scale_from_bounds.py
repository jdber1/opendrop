def scale_from_bounds(image_size, max_size, min_size=None):
    scale = 1

    if min_size is not None:
        if image_size.x < min_size.x or image_size.y < min_size.y:
            scale *= max(min_size.x/image_size.x, min_size.y/image_size.y)

            image_size *= scale

    if image_size.x > max_size.x or image_size.y > max_size.y:
        scale *= min(max_size.x/image_size.x, max_size.y/image_size.y)

    return scale
