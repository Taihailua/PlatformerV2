import os
import random

import math

import pygame

import sys

from scripts.utils import load_image, load_images, Animation
from scripts.entities import Player, Enemy
from scripts.tilemap import Tilemap
from scripts.clouds import Clouds
from scripts.particle import Particle
from scripts.spark import Spark


class Game:
    # constructor of class Game
    def __init__(self):
        pygame.init()  # Initialize pygame library, must init first before you can use pygame functions
        pygame.display.set_caption('Ninja Game')  # Set title
        self.screen = pygame.display.set_mode((640, 480))  # create game window 640p width and 480 height
        self.display = pygame.Surface((320, 240))  # Create game surface 320x240, this is where everything is drawn on

        self.clock = pygame.time.Clock()  # create object Clock to limit frame rate of the game

        self.movement = [False, False]  # this variable is used to track player's movement (left or right)
        # Create a dictionary to store all the games assets
        self.assets = {
            'decor': load_images('tiles/decor'),
            'grass': load_images('tiles/grass'),
            'large_decor': load_images('tiles/large_decor'),
            'stone': load_images('tiles/stone'),
            'player': load_image('entities/player.png'),
            'background': load_image('background_glacial_mountains_lightened.png'),
            'clouds': load_images('clouds'),
            'enemy/idle': Animation(load_images('entities/enemy/idle'), img_dur=6),
            'enemy/run': Animation(load_images('entities/enemy/run'), img_dur=4),
            'player/idle': Animation(load_images('entities/player/idle'), img_dur=6),
            'player/run': Animation(load_images('entities/player/run'), img_dur=4),
            'player/jump': Animation(load_images('entities/player/jump')),
            'player/slide': Animation(load_images('entities/player/slide')),
            'player/wall_slide': Animation(load_images('entities/player/wall_slide')),
            'particle/leaf': Animation(load_images('particles/leaf'), img_dur=20, loop=False),
            'particle/particle': Animation(load_images('particles/particle'), img_dur=6, loop=False),
            'gun': load_image('gun.png'),
            'projectile': load_image('projectile.png'),
        }

        self.clouds = Clouds(self.assets['clouds'], count=16)

        """ Create PhysicsEntity object represent the player,
            player's position (x=50, y=50) and size"""
        self.player = Player(self, (50, 50), (8, 15))
        # Create tile map object with size of 16pixels
        self.tilemap = Tilemap(self, tile_size=16)

        self.level = 0
        # load pre-made level/map
        self.load_level(0)

        self.picture = self.assets['background']
        self.picture = pygame.transform.scale(self.picture, (320, 240))

    def load_level(self, map_id):
        self.tilemap.load('PlatformerV2/data/maps/' + str(map_id) + '.json')
        self.leaf_spawners = []
        for tree in self.tilemap.extract([('large_decor', 2)], keep=True):
            # taking the position of the tile and looking for the area of the tree image that makes sense to spawn leaf
            # we offset it by 4 from the top left to the right, and 4 down from the top left
            # because we don't want the leaf to spawn out of nowhere from thin air
            # Rect(x, y, width, height)
            self.leaf_spawners.append(pygame.Rect(4 + tree['pos'][0], 4 + tree['pos'][1], 23, 13))

        # list of enemies
        self.enemies = []
        # we don't want to set keep to true because we only need the location to put stuff there
        for spawner in self.tilemap.extract([('spawners', 0), ('spawners', 1)]):
            # this is the players' spawner
            if spawner['variant'] == 0:
                self.player.pos = spawner['pos']
                # set air time to 0 to ensure the player not falling multiple times
                self.player.air_time = 0
            else:
                self.enemies.append(Enemy(self, spawner['pos'], (8, 15)))
        self.projectiles = []
        self.particles = []
        self.sparks = []
        # Scroll variable contains 2 values [scroll_x, scroll_y]
        # this variable is used to control the player's camera
        self.scroll = [0, 0]
        # set dead 0 by default
        self.dead = 0
        # when transition level set this variable to -30
        # when it -30 we want it to show completely black screen, and it will go all the way up to 0
        # use positive and negative number for transition is just a trick to keep track of the state
        # of the transition mathematically
        # when the absolute value of the transition is 0 that when you see everything
        # 30 is when you see nothing
        self.transition = -30

    def run(self):
        # infinite loop to keep the game running
        while True:
            # set background, this will clear the screen every frame too
            self.display.blit(self.picture, (0, 0))  # Change '.screen.' to display

            if not len(self.enemies):
                self.transition += 1
                if self.transition > 30:
                    # do this instead of += 1 to prevent the game from crash because of not enough map to use :)
                    # capping the number of level by using min
                    self.level = min(self.level + 1, len(os.listdir('PlatformerV2/data/maps')) - 1)
                    self.load_level(self.level)
            if self.transition < 0:
                self.transition += 1

            if self.dead:
                self.dead += 1
                if self.dead == 10:
                    self.transition = min(30, self.transition + 1)
                # set a timer as soon as you die after 40 frame about 2/3 a second reload the level
                if self.dead > 40:
                    self.load_level(self.level)
            """
self.scroll[0]:
self.player.rect().centerx: This gives the x-coordinate of the center of the player's sprite.
self.display.get_width() / 2: This gives half of the width of the display window, representing the center of the screen 
horizontally.
self.scroll[0]: This represents the current horizontal position of the camera.
So, (self.player.rect().centerx - self.display.get_width() / 2 - self.scroll[0]) calculates the difference between the 
center of the player's sprite and the center of the screen, adjusted by the current horizontal position of the camera.
THE SAME GOES FOR SELF.scroll[1]
"""
            # set camera for player
            self.scroll[0] += (self.player.rect().centerx - self.display.get_width() / 2 - self.scroll[0]) / 30
            self.scroll[1] += (self.player.rect().centery - self.display.get_height() / 2 - self.scroll[1]) / 30
            # set scroll value to integer to prevent inconsistent pixel in player sprite
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

            for rect in self.leaf_spawners:
                # random.random() random number between 0 and 1 - floating point number -
                # check to see if it less  than the pixel area of our rectangle
                # control portion of leaves, big tree = more leaves, small tree = fewer leaves
                # multiply it by 49999 to make it not every frame
                if random.random() * 49999 < rect.width * rect.height:
                    pos = (rect.x + random.random() * rect.width, rect.y + random.random() * rect.height)
                    # frame=random.randint(0, 20) give it random frame to start on so that we don't always start with
                    # the biggest leaf
                    self.particles.append(
                        Particle(self, 'leaf', pos, velocity=[-0.1, 0.3], frame=random.randint(0, 20)))

            self.clouds.update()
            self.clouds.render(self.display, offset=render_scroll)

            # render tile map on the display surface
            self.tilemap.render(self.display, offset=render_scroll)

            for enemy in self.enemies.copy():
                kill = enemy.update(self.tilemap, (0, 0))
                enemy.render(self.display, offset=render_scroll)
                if kill:
                    self.enemies.remove(enemy)

            if not self.dead:
                # update character's movement base on input from keyboard
                self.player.update(self.tilemap, (self.movement[1] - self.movement[0], 0))
                # render player sprite on the display surface
                self.player.render(self.display, offset=render_scroll)  # Change '.screen.' to display

            # [[x, y], direction, timer]
            # projectile[0][0] is the position
            # projectile[1] is the direction
            # and projectile[2] is the timer
            for projectile in self.projectiles.copy():
                projectile[0][0] += projectile[1]
                projectile[2] += 1
                img = self.assets['projectile']
                # when you subtract half of the width of something that just centers it
                self.display.blit(img, (projectile[0][0] - img.get_width() / 2 - render_scroll[0],
                                        projectile[0][1] - img.get_height() / 2 - render_scroll[1]))
                # if the position of projectile is a solid tile. remove the projectile
                if self.tilemap.solid_check(projectile[0]):
                    self.projectiles.remove(projectile)
                    for i in range(4):
                        # (math.pi if projectile[1] > 0) means
                        # the spark shoot left only if the projectile is going right
                        self.sparks.append(
                            Spark(projectile[0], random.random() - 0.5 + (math.pi if projectile[1] > 0 else 0),
                                  2 + random.random()))
                # if projectile lasts longer than 360 pixels (6 seconds), remove projectile
                elif projectile[2] > 360:
                    self.projectiles.remove(projectile)
                # if the player is dashing, they'll become invincible
                elif abs(self.player.dashing) < 50:
                    if self.player.rect().collidepoint(projectile[0]):
                        self.projectiles.remove(projectile)
                        self.dead += 1
                        for i in range(30):
                            angle = random.random() * math.pi * 2
                            speed = random.random() * 5
                            self.sparks.append(Spark(self.player.rect().center, angle, 2 + random.random()))
                            self.particles.append(Particle(self, 'particle', self.player.rect().center,
                                                           velocity=[math.cos(angle + math.pi) * speed * 0.5,
                                                                     math.sin(angle + math.pi) * speed * 0.5],
                                                           frame=random.randint(0, 7)))

            # vfx when player *dies*
            for spark in self.sparks.copy():
                kill = spark.update()
                spark.render(self.display, offset=render_scroll)
                if kill:
                    self.sparks.remove(spark)

            # function for particle management
            for particle in self.particles.copy():
                kill = particle.update()
                particle.render(self.display, offset=render_scroll)
                if particle.type == 'leaf':
                    # make the leaves fall naturally - fall in a sin graph
                    # multiply by 0.035 to make it move slower
                    # multiply by 0.3 to make the curve in sin graph smaller
                    particle.pos[0] += math.sin(particle.animation.frame * 0.035) * 0.3
                if kill:
                    self.particles.remove(particle)

            # print(self.tilemap.physics_rects_around(self.player.pos))
            """Learn about this and then you can use it 
            pygame.Rect(*self.img_pos, *self.img.get_size())"""
            # Loop for every pygame events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:  # Set event when pressing key down
                    if event.key == pygame.K_LEFT:
                        self.movement[0] = True
                    if event.key == pygame.K_RIGHT:
                        self.movement[1] = True
                    if event.key == pygame.K_SPACE:
                        self.player.jump()
                    if event.key == pygame.K_x:
                        self.player.dash()
                if event.type == pygame.KEYUP:  # Set event when releasing a key
                    if event.key == pygame.K_LEFT:
                        self.movement[0] = False
                    if event.key == pygame.K_RIGHT:
                        self.movement[1] = False

            # if not transition yet then wait
            # this code is expensive in terms of performance because you are generating another surface, draw circle
            # and then blit it on the display
            if self.transition:
                # Create a black surface size of the display
                transition_surf = pygame.Surface(self.display.get_size())
                # the trick for transition is we draw a circle on the surface
                # ,and then we set the color key of the surface to the color of the circle
                # that way the circle we draw is a transparent part
                # so when we blit the surface on top of the screen you can can't see the outer edge outside the circle
                # * 8 is to ensure the circle can expand with proper size
                pygame.draw.circle(transition_surf, (255, 255, 255),
                                   (self.display.get_width() // 2, self.display.get_height() // 2), (30 - abs(self.transition) * 8))
                transition_surf.set_colorkey((255, 255, 255))
                self.display.blit(transition_surf, (0, 0))
            # Scale the screen to a smaller display
            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))
            # Update the screen with every change made
            pygame.display.update()
            self.clock.tick(60)


class StartMenu:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.Font(None, 36)  # Define font for menu text
        self.selected_option = 0  # Keep track of currently selected option
        self.options = ["Start", "Quit"]  # Menu options
        self.background = pygame.image.load("PlatformerV2/menu_background.png")  # Load background image
        # Scale the background image to match the size of the display
        self.background = pygame.transform.scale(self.background, (screen.get_width(), screen.get_height()))

    def draw(self):
        self.screen.blit(self.background, (0, 0))  # Draw background image
        for i, option in enumerate(self.options):
            text = self.font.render(option, True, (255, 255, 255))  # Render menu text
            text_rect = text.get_rect(center=(320, 200 + i * 50))  # Position text in the center
            self.screen.blit(text, text_rect)  # Draw text on screen

            if i == self.selected_option:  # Highlight selected option
                pygame.draw.circle(self.screen, (255, 255, 255), (text_rect.left - 20, text_rect.centery), 5)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:  # Move selection up
                    self.selected_option = (self.selected_option - 1) % len(self.options)
                elif event.key == pygame.K_DOWN:  # Move selection down
                    self.selected_option = (self.selected_option + 1) % len(self.options)
                elif event.key == pygame.K_RETURN:  # Execute selected option
                    if self.selected_option == 0:  # Start the game
                        return "start_game"
                    elif self.selected_option == 1:  # Quit the game
                        pygame.quit()
                        sys.exit()
        return None


def main():
    pygame.init()
    pygame.mixer.init()  # Initialize the mixer
    pygame.mixer.music.load('PlatformerV2/data/music.wav')  # Load the background music. Replace 'background_music.mp3' with the path to your music file.
    pygame.mixer.music.play(-1)  # Play the music. -1 means loop indefinitely.

    screen = pygame.display.set_mode((900, 506))  # Set screen size to match the background image
    pygame.display.set_caption('Ninja Game')
    # Load and set icon
    icon = pygame.image.load('PlatformerV2/icon.png')  # Replace 'game_icon.png' with the path to your icon image
    pygame.display.set_icon(icon)
    clock = pygame.time.Clock()
    start_menu = StartMenu(screen)

    while True:
        action = start_menu.handle_events()  # Handle menu events
        if action == "start_game":  # If "Start" is selected, break out of the loop and start the game
            break
        start_menu.draw()  # Draw the menu
        pygame.display.update()
        clock.tick(60)

    # Start the game
    font = pygame.font.Font(None, 36)  # Create a font object. None means the default font, and 36 is the size.
    text = font.render("Defeat all enemies!", True, (255, 255, 255))  # Create a Surface with the text. The second argument is anti-aliasing, and the third is the color (white).
    
    screen.fill((0, 0, 0))  # Fill the screen with black
    screen.blit(text, (450 - text.get_width() // 2, 253 - text.get_height() // 2))  # Display the text at the center of the screen
    pygame.display.update()  # Update the display
    pygame.time.delay(1000)  # Wait for 3000 milliseconds (3 seconds)

    Game().run()


if __name__ == "__main__":
    main()