import os

import pygame
# global variable represents path to folder contain the img
BASE_IMG_PATH = 'data/images/'


def load_image(path):
    # Using convert will make rendering more efficient
    img = pygame.image.load(BASE_IMG_PATH + path).convert()
    img.set_colorkey((0, 0, 0))  # transparency
    return img


def load_images(path):
    # empty list to store all downloaded images
    images = []
    # loop to scan every file in the folder given by object 'path'
    # 'data/images/ ' + path
    for img_name in os.listdir(BASE_IMG_PATH + path):
        # using load_image function to load image and then add it to images list
        images.append(load_image(path + '/' + img_name))
    return images

class Animation:
    # Search google how to make each frame is one image

    """Parameters:
    images: A list of images that make up the animation sequence. Each image represents a single frame of the animation.
    img_dur: The duration (in frames) each image should be displayed. Default is 5 frames.
    loop: A boolean indicating whether the animation should loop continuously. Default is True.
    Attributes:
    self.images: Stores the list of images for the animation.
    self.loop: Stores whether the animation should loop.
    self.img_duration: Stores the duration each image should be displayed.
    self.done: A boolean flag indicating whether the animation has finished playing.
    self.frame: Stores the current frame of the animation."""
    def __init__(self, images, img_dur=5, loop=True):
        self.images = images
        self.loop = loop
        self.img_duration = img_dur
        self.done = False
        self.frame = 0

    def copy(self):
        return Animation(self.images, self.img_duration, self.loop)

    """Updates the animation by advancing the frame.
        If loop is True, the frame index wraps around to the beginning when reaching the end of the animation sequence.
        If loop is False, the animation stops when it reaches the end.
        Sets self.done to True if the animation has finished playing."""
    def update(self):
        if self.loop:
            self.frame = (self.frame + 1) % (self.img_duration * len(self.images))
        else:
            self.frame = min(self.frame + 1, self.img_duration * len(self.images) - 1)
            if self.frame >= self.img_duration * len(self.images) - 1:
                self.done = True
    """Returns the image corresponding to the current frame of the animation.
    Calculates the index of the current frame based on the current frame number (self.frame) 
    and the image duration (self.img_duration).
    Returns the corresponding image from the images list."""
    def img(self):
        return self.images[int(self.frame / self.img_duration)]

