import pygame

import sys

from scripts.utils import load_images
from scripts.tilemap import Tilemap

RENDER_SCALE = 2.0


class Editor:
    # constructor of class Game
    def __init__(self):
        pygame.init()  # Initialize pygame library, must init first before you can use pygame functions
        pygame.display.set_caption('editor')  # Set title
        self.screen = pygame.display.set_mode((640, 480))  # create game window 640p width and 480 height
        self.display = pygame.Surface((320, 240))  # Create game surface 320x240, this is where everything is drawn on

        self.clock = pygame.time.Clock()  # create object Clock to limit frame rate of the game

        self.assets = {
            'decor': load_images('tiles/decor'),
            'grass': load_images('tiles/grass'),
            'large_decor': load_images('tiles/large_decor'),
            'stone': load_images('tiles/stone'),
            'spawners': load_images('tiles/spawners'),

        }

        self.movement = [False, False, False, False]

        # Create tile map object with size of 16pixels
        self.tilemap = Tilemap(self, tile_size=16)

        try:
            self.tilemap.load('map.json')
        except FileNotFoundError:
            pass

        # Scroll variable contains 2 values [scroll_x, scroll_y]
        # this variable is used to control the player's camera
        self.scroll = [0, 0]

        # list that stores all the tile
        self.tile_list = list(self.assets)
        # index represent which group of tile
        self.tile_group = 0
        # index represent which variant of that tile
        self.tile_variant = 0

        # LMC (left mouse click)
        self.clicking = False
        # RMC (right mouse click)
        self.right_clicking = False
        self.shift = False
        self.ongrid = True

    def run(self):
        # infinite loop to keep the game running
        while True:
            # set background, this will clear the screen every frame too
            self.display.fill((0, 0, 0))  # Change '.screen.' to display

            """[1] is holding right 
            minus [2] is holding left
            [3] is holding down
            minus [4] is holding up
            multiply by 2 to make it move faster"""
            self.scroll[0] += (self.movement[1] - self.movement[0]) * 2
            self.scroll[1] += (self.movement[3] - self.movement[2]) * 2

            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

            self.tilemap.render(self.display, offset=render_scroll)

            # we're taking tiles from self.tile_list
            # self.tile_group is integer represent the index for the type of tile in the list ex:0=>decor, 1=>grass...
            # self.tile_variant is another index for the variant of that tile
            current_tile_img = self.assets[self.tile_list[self.tile_group]][self.tile_variant].copy()
            # set_alpha(100) will make it partially transparent
            # set to 0 will make it fully transparent and 255 it'll be fully opaque-completely visible
            current_tile_img.set_alpha(100)

            # using mouse position to place the tile
            mpos = pygame.mouse.get_pos()
            # divide RENDER_SCALE because we are scaling the screen to a smaller display (640x480 to 320x240)
            mpos = (mpos[0] / RENDER_SCALE, mpos[1] / RENDER_SCALE)
            # return the mouse position to the tile_pos
            tile_pos = (int((mpos[0] + self.scroll[0]) // self.tilemap.tile_size),
                        int((mpos[1] + self.scroll[1]) // self.tilemap.tile_size))

            if self.ongrid:
                """this function takes the tile_pos we just define up there 
                , convert it back to pixel coordinate by multiply it by tile_size 
                and adjust the position base on the camera for rendering"""
                self.display.blit(current_tile_img, (tile_pos[0] * self.tilemap.tile_size - self.scroll[0],
                                                     tile_pos[1] * self.tilemap.tile_size - self.scroll[1]))
            else:
                self.display.blit(current_tile_img, mpos)

            # function to place a tile using LMC base on mouse position
            if self.clicking and self.ongrid:
                self.tilemap.tilemap[str(tile_pos[0]) + ';' + str(tile_pos[1])] = {
                    'type': self.tile_list[self.tile_group], 'variant': self.tile_variant, 'pos': tile_pos}

            # function to delete a tile using RMC base on mouse position
            # tilemap.tilemap explain: .tilemap is attribute of tilemap object
            if self.right_clicking:
                tile_loc = str(tile_pos[0]) + ';' + str(tile_pos[1])
                if tile_loc in self.tilemap.tilemap:
                    del self.tilemap.tilemap[tile_loc]
                for tile in self.tilemap.offgrid_tiles.copy():
                    tile_img = self.assets[tile['type']][tile['variant']]
                    tile_r = pygame.Rect(tile['pos'][0] - self.scroll[0], tile['pos'][1] - self.scroll[1], tile_img.get_width(), tile_img.get_height())
                    # if this tile is "collide" with our mouse
                    if tile_r.collidepoint(mpos):
                        self.tilemap.offgrid_tiles.remove(tile)


            # draw the current tile we currently use on the top left of the screen
            self.display.blit(current_tile_img, (5, 5))

            """Learn about this and then you can use it 
            pygame.Rect(*self.img_pos, *self.img.get_size())"""
            # Loop for every pygame events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    # 1 is LMC (left mouse click)
                    if event.button == 1:
                        self.clicking = True
                        if not self.ongrid:
                            # subtract self.scroll to convert currently display window space back to the world space
                            """for example
                             From your camera is at 100 pixel to the right (100, y)
                             and you want to add tile at top left (0, y) of 
                            current window space but in the real world space that top left is actually (100, y)
                            that explain why you need to add in self.scroll[0] and [1]
                            """
                            self.tilemap.offgrid_tiles.append(
                                {'type': self.tile_list[self.tile_group], 'variant': self.tile_variant,
                                 'pos': (mpos[0] + self.scroll[0], mpos[1] + self.scroll[1])})
                    # 2 is the mouse wheel
                    # 3 is RMC (right mouse click)
                    if event.button == 3:
                        self.right_clicking = True

                    if self.shift:
                        # 4 is scrolling mouse wheel up and 5 is down
                        # use mouse wheel to scroll through the tile list
                        if event.button == 4:
                            # using modular for looping
                            # when you reach the end of that list it just loop around to 0 and if less than 0 is the end
                            self.tile_variant = (self.tile_variant - 1) % len(
                                self.assets[self.tile_list[self.tile_group]])
                        if event.button == 5:
                            self.tile_variant = (self.tile_variant + 1) % len(
                                self.assets[self.tile_list[self.tile_group]])
                    else:
                        if event.button == 4:
                            self.tile_group = (self.tile_group - 1) % len(self.tile_list)
                            # set variant back to 0 to prevent out of range loop and to jump to the next tile_group
                            self.tile_variant = 0
                        if event.button == 5:
                            self.tile_group = (self.tile_group + 1) % len(self.tile_list)
                            self.tile_variant = 0

                # these clicking variable will be updated based on our mouse state
                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.clicking = False
                    if event.button == 3:
                        self.right_clicking = False

                if event.type == pygame.KEYDOWN:  # Set event when pressing key down
                    if event.key == pygame.K_a:
                        self.movement[0] = True
                    if event.key == pygame.K_d:
                        self.movement[1] = True
                    if event.key == pygame.K_w:
                        self.movement[2] = True
                    if event.key == pygame.K_s:
                        self.movement[3] = True
                    # set key for ongrid variable represent whether we want to draw the tile on grid or not
                    # if press G self.ongrid will flip itself True=>False, False=>True
                    if event.key == pygame.K_g:
                        self.ongrid = not self.ongrid
                    if event.key == pygame.K_t:
                        self.tilemap.autotile()
                    if event.key == pygame.K_o:
                        self.tilemap.save('map.json')
                    if event.key == pygame.K_LSHIFT:
                        self.shift = True
                if event.type == pygame.KEYUP:  # Set event when releasing a key
                    if event.key == pygame.K_a:
                        self.movement[0] = False
                    if event.key == pygame.K_d:
                        self.movement[1] = False
                    if event.key == pygame.K_w:
                        self.movement[2] = False
                    if event.key == pygame.K_s:
                        self.movement[3] = False
                    if event.key == pygame.K_LSHIFT:
                        self.shift = False
            # Scale the screen to a smaller display
            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))
            # Update the screen with every change made
            pygame.display.update()
            self.clock.tick(60)


Editor().run()
