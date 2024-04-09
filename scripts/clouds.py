import random


class Cloud:
    # Cloud Constructor
    def __init__(self, pos, img, speed, depth):
        self.pos = list(pos)
        self.img = img
        self.speed = speed
        self.depth = depth

    # update the position of the cloud based on its speed, by incrementing X-axis by its speed
    def update(self):
        self.pos[0] += self.speed

    # render the cloud onto the surface(surf)
    def render(self, surf, offset=(0, 0)):
        # subtract offset value for camera work and multiply by depth to create parallax effect
        render_pos = (self.pos[0] - offset[0] * self.depth, self.pos[1] - offset[1] * self.depth)
        """The position is adjusted using modulo operations (%) to create a tiling effect. This ensures that if the 
        image moves beyond the boundaries of the surface, it wraps around to the opposite side, 
        giving the appearance of a seamless scrolling background.
        (surf.get_width() + self.img.get_width()) and (surf.get_height() + self.img.get_height()) calculate the width 
        and height of the tiled area. The image will wrap around within these dimensions.
        Finally, the image is blitted onto the surface with its position adjusted based on the modulo calculations. 
        The adjustments (- self.img.get_width() and - self.img.get_height()) are made 
        to ensure that the image is correctly positioned within the tiled area."""
        surf.blit(self.img, (render_pos[0] % (surf.get_width() + self.img.get_width()) - self.img.get_width(),
                             render_pos[1] % (surf.get_height() + self.img.get_height()) - self.img.get_height()))


class Clouds:
    # Clouds constructor
    # count is the number of cloud to create
    def __init__(self, cloud_images, count=16):
        self.clouds = []
        # each iteration create a cloud to add to the list
        # random.random() : random float between 0 and 1
        for i in range(count):
            self.clouds.append(Cloud((random.random() * 99999, random.random() * 99999), random.choice(cloud_images),
                                     random.random() * 0.05 + 0.05, random.random() * 0.6 + 0.2))
        # Advanced coding technique
        """After creating all the clouds, they are sorted based on their depth using a lambda function as the key 
        for sorting
        . This ensures that clouds 
        with higher depth (closer to the viewer) appear in front of clouds with lower depth."""""
        self.clouds.sort(key=lambda x: x.depth)

    # update every cloud in the collection by calling update method in class Cloud
    # , this will make each cloud move horizontally
    def update(self):
        for cloud in self.clouds:
            cloud.update()

    # render all the clouds in clouds list onto the surface by calling render method in class cloud
    def render(self, surf, offset=(0, 0)):
        for cloud in self.clouds:
            cloud.render(surf, offset=offset)
