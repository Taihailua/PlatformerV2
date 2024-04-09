import random

import math

import pygame

from scripts.particle import Particle
from scripts.spark import Spark


class PhysicsEntity:
    def __init__(self, game, e_type, pos, size):
        self.game = game
        self.type = e_type
        self.pos = list(pos)
        self.size = size
        self.velocity = [float(0), float(0)]
        # object to detect which direction had a collision
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}
        self.action = ''
        self.anim_offset = (-3, -3)
        self.flip = False
        self.set_action('idle')  # Set which animation we're currently using

        self.last_movement = [0, 0]

    def rect(self):
        # using top left position of the player sprite to handle physics
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])

    # Set action function
    #
    def set_action(self, action):
        # Only set action when the action we're currently using is changed
        if action != self.action:
            self.action = action
            # update animation
            # example for 'self.type + '/' + self.action': player/run, player/slide....
            # .copy() creates a new instance of that animation
            self.animation = self.game.assets[self.type + '/' + self.action].copy()

    def update(self, tilemap, movement=(0, 0)):
        """we're resetting every frame so every time update function is called
         ,'self.collisions' got reset back to false"""
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}

        frame_movement = (movement[0] + self.velocity[0], movement[1] + self.velocity[1])  # Formula for movement

        # separating the movement to handle 2 collision per frame
        # ,so you can handle collision from moving up/down or left/right
        # 2 pos represent 2 dimension movement [0] is x and [1] is y
        self.pos[0] += frame_movement[0]  # update X movement

        """Every one frame we got a collision the value will be true
        ,if we hold down the button and collide with the wall
        . when release it'll return to false because we're only standing next to it"""

        entity_rect = self.rect()

        # loop to scan nearby tiles
        for rect in tilemap.physics_rects_around(self.pos):
            # if collision is detected
            if entity_rect.colliderect(rect):
                # if entity right border collides with tiles right border, it will stop
                if frame_movement[0] > 0:  # positive X is moving right
                    entity_rect.right = rect.left
                    self.collisions['right'] = True
                # same goes for left border
                if frame_movement[0] < 0:  # negative X is moving left
                    entity_rect.left = rect.right
                    self.collisions['left'] = True
                self.pos[0] = entity_rect.x

        self.pos[1] += frame_movement[1]  # update Y movement
        entity_rect = self.rect()
        # loop to scan nearby tiles
        for rect in tilemap.physics_rects_around(self.pos):
            # if collision is detected
            if entity_rect.colliderect(rect):
                # if entity right border collides with tiles right border, it will stop
                if frame_movement[1] > 0:  # positive y is moving down
                    entity_rect.bottom = rect.top
                    self.collisions['down'] = True
                # same goes for left border
                if frame_movement[1] < 0:  # negative y is moving up
                    entity_rect.top = rect.bottom
                    self.collisions['up'] = True
                self.pos[1] = entity_rect.y

        # if moving right set flip to false because our img is already facing right
        if movement[0] > 0:
            self.flip = False
        # if moving left set flip to true to flip img because our img is currently facing right
        if movement[0] < 0:
            self.flip = True

        # this movement variable is keeping track of movement which is the input to the update
        # not the actual movement that was executed upon
        self.last_movement = movement

        # If falling speed is smaller than 5 then it will take smaller value
        # If greater than 5 then velocity will be 5 because velocity cap at 5
        # this is Y velocity
        self.velocity[1] = min(5.0, self.velocity[1] + 0.1)

        # we're not using X velocity, yet
        # reset velocity back to zero if we're standing on a tile
        if self.collisions['down'] or self.collisions['up']:
            self.velocity[1] = 0

        self.animation.update()

    def render(self, surf, offset=(0, 0)):
        # this function will output image appropriate to our currently action
        surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False),
                  (self.pos[0] - offset[0] + self.anim_offset[0], self.pos[1] - offset[1] + self.anim_offset[1]))


"""Why we're inheriting our code here is because different type of entity
will have different animation logic, so we are writing animation logic for our player
That is why we separate it with inheritance"""


# idea for the enemy
# they can walk around but can't walk off the edge of the tile
# they can turn around and have a basic AI for casually walking around
# and shoot at the player base on the location of the player whether the shot will line up
# the enemy can only shoot horizontally when the player is at the right level in the Y axis
# and a timer to keep track of how long the enemy should be moving
class Enemy(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'enemy', pos, size)

        self.walking = 0

    def update(self, tilemap, movement=(0, 0)):
        # if enemy is walking
        if self.walking:
            # scanning out in front of the direction you're facing -7/7 pixel in front
            # , check below the ground(self.pos[1] + 23)
            # this code is only used to prevent the enemy from walking off the edge not turning around when hit a wall
            if tilemap.solid_check((self.rect().centerx + (-7 if self.flip else 7), self.pos[1] + 23)):
                # if the enemies hit something on their right or left, they'll turn around
                if (self.collisions['right'] or self.collisions['left']):
                    self.flip = not self.flip
                else:
                    # subtract movement by 0.5 if the enemy is facing left
                    # otherwise add 0.5
                    movement = (movement[0] - 0.5 if self.flip else 0.5, movement[1])
            else:
                self.flip = not self.flip
            # cut down the walking to 0 slowly over time if they're walking
            self.walking = max(0, self.walking - 1)
            if not self.walking:
                # calculate the distance between the player and the enemy
                dis = (self.game.player.pos[0] - self.pos[0], self.game.player.pos[1] - self.pos[1])
                # if the Y axis offset between the player and the enemy is less than 16
                if (abs(dis[1]) < 16):
                    # if the player is to the left of the enemy the distance you will get is a negative number
                    # if the enemy is looking left and the player is to the left of the enemy
                    # , the enemy will be able to shoot
                    if (self.flip and dis[0] < 0):
                        # - 7 in X axis position and -1,5 in speed is because they're facing left
                        self.game.projectiles.append([[self.rect().centerx - 7, self.rect().centery], -1.5, 0])
                        for i in range(4):
                            self.game.sparks.append(
                                Spark(self.game.projectiles[-1][0], random.random() - 0.5 + math.pi, 2 + random.random()))

                    # if the player is to the right and the enemy is looking right
                    if (not self.flip and dis[0] > 0):
                        # the other way around for facing right
                        self.game.projectiles.append([[self.rect().centerx + 7, self.rect().centery], 1.5, 0])
                        for i in range(4):
                            self.game.sparks.append(
                                Spark(self.game.projectiles[-1][0], random.random() - 0.5, 2 + random.random()))
        # if not walking
        # check if this random number between 0 and 1 is lesser than 0.01 or not (1/100 chance of occurring)
        # since we're running at 60fps means 1 in every 1.67s if the enemy is not walking
        elif random.random() < 0.01:
            # then walking will be set to a random number
            # (30, 120) is the number of frame to continue to walk for which is the random number from 0.5 to 2 seconds
            self.walking = random.randint(30, 120)

        super().update(tilemap, movement=movement)

        # if the enemies are moving set action to run
        if movement[0] != 0:
            self.set_action('run')
        # else set to idle
        else:
            self.set_action('idle')
        # while player is dashing
        if abs(self.game.player.dashing) >= 50:
            # if rect of the enemy collide with player rect
            if self.rect().colliderect(self.game.player.rect()):
                for i in range(30):
                    angle = random.random() * math.pi * 2
                    speed = random.random() * 5
                    self.game.sparks.append(Spark(self.rect().center, angle, 2 + random.random()))
                    self.game.particles.append(Particle(self.game, 'particle', self.rect().center,
                                                   velocity=[math.cos(angle + math.pi) * speed * 0.5,
                                                             math.sin(angle + math.pi) * speed * 0.5],
                                                   frame=random.randint(0, 7)))
                self.game.sparks.append(Spark(self.rect().center, 0, 5 + random.random()))
                self.game.sparks.append(Spark(self.rect().center, math.pi, 5 + random.random()))

                return True


    def render(self, surf, offset=(0, 0)):
        super().render(surf, offset=offset)

        if self.flip:
            # flip the gun in X axis (True) and don't flip in Y axis (False)
            # self.rect().centerx - 4 (4 is 4 pixels) is to off set the gun and put it at the correct spot
            # subtract for gun width to account for the gun image because we render the gun
            # from the perspective of the top left when facing right and top right when facing left
            surf.blit(pygame.transform.flip(self.game.assets['gun'], True, False),
                      (self.rect().centerx - 4 - self.game.assets['gun'].get_width() - offset[0],
                       self.rect().centery - offset[1]))
        else:
            surf.blit(self.game.assets['gun'], (self.rect().centerx + 4 - offset[0], self.rect().centery - offset[1]))


class Player(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'player', pos, size)
        # this variable is used to keep track of how long we've been in the air
        self.air_time = 0
        # The player will have one jump, a wall-jump will consume that one jump
        # but if you're on a wall, you out of that one jump, you still can jump out of that wall - wall jump :) -
        # you can jump and jump off a wall, if you jump and fall off a wall then you can't jump again
        self.jumps = 1
        self.wall_slide = False
        self.dashing = 0

    def update(self, tilemap, movement=(0, 0)):
        super().update(tilemap, movement=movement)

        self.air_time += 1
        # when the player falls off the map for over 3 seconds
        # set player dead
        if self.air_time > 120:
            self.game.dead += 1

        # Check if player is standing on a tile
        if self.collisions['down']:
            self.air_time = 0
            self.jumps = 1

        # this variable will act as a single frame switch
        # if active as true it will true for the rest of that frame
        # when update is called again it will be false again
        self.wall_slide = False
        # if we hit the wall on either side and we in the air then we're sliding on that wall
        # only in the frame where this condition is true then in that frame will wall_slide be true
        if (self.collisions['right'] or self.collisions['left']) and self.air_time > 4:
            self.wall_slide = True
            # we're capping the downward velocity at 0.5
            # if velocity[1] smaller than 0.5 then it will take velocity[1]
            # if velocity[1] greater than 0.5 then it will take 0.5
            self.velocity[1] = min(self.velocity[1], 0.5)
            # if we're facing right(when wall slide) then flip is false, if left then flip true
            if self.collisions['right']:
                self.flip = False
            else:
                self.flip = True
            self.set_action('wall_slide')

        # setting restriction for wall slide
        # if we're wall slide we don't want it to switch to any of these animations
        if not self.wall_slide:
            # if air time > 4(pixel) and velocity[1] < 0
            # , it will change action to 'jump' and use corresponding animation for it
            if self.air_time > 4:
                self.set_action('jump')
            # if movement in X axis not 0 then set action to run and use corresponding animation for it
            elif movement[0] != 0:
                self.set_action('run')
            else:
                self.set_action('idle')
        # why put this condition before our 'timer'
        # if we don't put it before the timer then when dashing is set to 60/-60 the timer will change it to 59/-59
        # then we will only have the end burst but no initial burst
        if abs(self.dashing) in {60, 50}:
            # create 20 particle in random direction with random speed (this is our burst)
            for i in range(20):
                # we're taking a random angle
                # random.random()-floating point between 0 and 1-multiply by 2π is just full circle of angle(in radiant)
                # random.random() is just selecting a random angle in that circle
                # if we multiply by a random number instead of 2π then the particle will be unevenly distributed
                # but if we  put a big number like 9999999 it will still work but just do 2π please
                angle = random.random() * math.pi * 2
                # create random speed
                speed = random.random() * 0.5 + 0.5
                # generate a velocity base on the angle
                # this is how you move things in a direction pretty much in any case in 2D
                # just memorize this one formular, it will get you through most trigonometry in game
                """Important !!! if you want to make something look natural in game development use math"""
                # why go through all this math and hassle
                # ,just to generate a random direction and to create a particle velocity ?
                # because with random number the scaling and distributing of particle may cause wierd particle
                # and unevenly distributed amount of particle
                pvelocity = [math.cos(angle) * speed, math.sin(angle) * speed]
                # use the center of the player to spawn particle
                self.game.particles.append(Particle(self.game, 'particle', self.rect().center, velocity=pvelocity
                                                    , frame=random.randint(0, 7)))

        # this code will eventually bring self.dashing back to 0
        # this also serves as a timer
        if self.dashing > 0:
            self.dashing = max(0, self.dashing - 1)
        if self.dashing < 0:
            self.dashing = min(0, self.dashing + 1)

        # at the end of our first ten frames of the dash we're going severely cut down on the X axis velocity
        # 50 will also serve as a cooldown - about 5 to 6 seconds
        # when on cooldown you can't dash again ofc :)
        # abs(self.dashing) accounts for both direction (left n right)
        if abs(self.dashing) > 50:
            # abs(self.dashing) / self.dashing will return either 1 or -1
            # multiply by 8 is to modify the distance
            self.velocity[0] = abs(self.dashing) / self.dashing * 8
            # here is where the cut down begin
            # the purpose of this code is to cause a sudden stop in the dash
            if abs(self.dashing) == 51:
                self.velocity[0] *= 0.1
            # abs dashing/dashing gives the direction of the particle
            # and random.random() * 3 will make the particle move along instead of stay stationary
            pvelocity = [abs(self.dashing) / self.dashing * random.random() * 3, 0]
            self.game.particles.append(Particle(self.game, 'particle', self.rect().center, velocity=pvelocity
                                                , frame=random.randint(0, 7)))

        # the remaining velocity from dashing will quickly be diminished by this code right here
        if self.velocity[0] > 0:
            # subtract 0.1 every frame from the velocity if it's greater than 0 and stop it from going below 0
            # this is for wall jump while facing left
            self.velocity[0] = max(self.velocity[0] - 0.1, 0)
        else:
            # add 0.1 every frame from the velocity if it's lesser than 0 and stop it from going below 0
            # this is for wall jump while facing right
            self.velocity[0] = min(self.velocity[0] + 0.1, 0)

    def jump(self):
        if self.wall_slide:
            # if we're wall sliding and facing left
            if self.flip and self.last_movement[0] < 0:
                # set X axis velocity to 3.5 act as impulse pushing us to the right away from the wall
                self.velocity[0] = 3.5
                # set Y axis velocity to -2.5 force us up, the value is smaller than normal jump because in wall slide
                # we don't want to jump as high as normal jump
                self.velocity[1] = -2.5
                self.air_time = 5
                # we want the jump to be consumed if we have one remaining by the wall jump
                self.jumps = max(0, self.jumps - 1)
                return True
            elif not self.flip and self.last_movement[0] > 0:
                self.velocity[0] = -3.5
                self.velocity[1] = -2.5
                self.air_time = 5
                self.jumps = max(0, self.jumps - 1)
                return True

        # remember 0 return false
        # if self.jumps = 0 means if False:
        elif self.jumps:
            self.velocity[1] = -3
            self.jumps -= 1
            # set air time to five to quickly transition to 'jump' action
            # because 'if self.air_time > 4:
            #             self.set_action('jump')'
            self.air_time = 5
            return True

    # the idea of dash is we disappear into a string of particle
    # ,so we need to overwrite -build another render function on top of it- the render function of class PhysicEntity
    def render(self, surf, offset=(0, 0)):
        # if we're not in the first ten frames of a dash (if a dash is on cooldown or not cooldown at all)
        # we'll go invisible (not render the player) in that first 10 frames
        if abs(self.dashing) <= 50:
            super().render(surf, offset=offset)

    def dash(self):
        # variable dashing will keep track of how much we want to dash and which direction

        if not self.dashing:
            # if facing left
            if self.flip:
                # 60 is how much we want to dash
                # minus 60 means moving left in X axis
                self.dashing = -60
            else:
                # facing right and dash to the right
                self.dashing = 60
