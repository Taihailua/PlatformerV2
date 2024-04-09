import json
import pygame

# tips and trick from tutor
# rule for auto tile
AUTOTILE_MAP = {
    tuple(sorted([(1, 0), (0, 1)])): 0,
    tuple(sorted([(1, 0), (0, 1), (-1, 0)])): 1,
    tuple(sorted([(-1, 0), (0, 1)])): 2,
    tuple(sorted([(-1, 0), (0, -1), (0, 1)])): 3,
    tuple(sorted([(-1, 0), (0, -1)])): 4,
    tuple(sorted([(-1, 0), (0, -1), (1, 0)])): 5,
    tuple(sorted([(1, 0), (0, -1)])): 6,
    tuple(sorted([(1, 0), (0, -1), (0, 1)])): 7,
    tuple(sorted([(1, 0), (-1, 0), (0, 1), (0, -1)])): 8,
}

"""
NEIGHBOR_OFFSETS: list contains relative coordinates that represent the positions of neighboring tiles in a grid system
. Each tuple in the list represents an offset from the current tile position to one of its neighboring tiles. 
(-1, 0): Move left by one tile.
(-1, -1): Move diagonally up and to the left by one tile.
(0, -1): Move up by one tile.
(1, -1): Move diagonally up and to the right by one tile.
(1, 0): Move right by one tile.
(0, 0): Stay in the current tile (center).
(-1, 1): Move diagonally down and to the left by one tile.
(0, 1): Move down by one tile.
(1, 1): Move diagonally down and to the right by one tile."""
NEIGHBOR_OFFSETS = [(-1, 0), (-1, -1), (0, -1), (1, -1), (1, 0), (0, 0), (-1, 1), (0, 1), (1, 1)]
PHYSIC_TILES = {'grass', 'stone'}  # this is a set using this is more optimized
AUTOTILE_TYPES = {'grass', 'stone'}


class Tilemap:
    def __init__(self, game, tile_size=16):
        self.game = game
        self.tile_size = tile_size
        self.tilemap = {}
        self.offgrid_tiles = []

    # function to get specific location of the tile we are trying to find
    # our tiles are in tile type format along with tile variant, those 2 go together to uniquely indentify the tile type
    # id_pair is one of those 2 combine, id_pairs is a list of those
    # this function will take a bunch of type of tile we're looking for, told us where they are and their information

    def extract(self, id_pairs, keep=False):
        matches = []
        # why use copy() ? because we might want to delete that tile from the list if we're not keeping it
        for tile in self.offgrid_tiles.copy():
            # if found the id_pair we're looking for, it will give us that tile information
            if (tile['type'], tile['variant']) in id_pairs:
                matches.append(tile.copy())
                # if we don't want to keep that tile then we will remove it from off grid tile
                if not keep:
                    self.offgrid_tiles.remove(tile)

        for loc in self.tilemap:
            tile = self.tilemap[loc]
            if (tile['type'], tile['variant']) in id_pairs:
                matches.append(tile.copy())
                # we're changing the position for the tile we're referencing because we want it to be in pixel
                # because the tile map is in tile coordinate for the grid not in pixel
                # why we use copy() again because we want to work with the copy of that tile not that exact tile
                matches[-1]['pos'] = matches[-1]['pos'].copy()
                matches[-1]['pos'][0] *= self.tile_size
                matches[-1]['pos'][1] *= self.tile_size
                if not keep:
                    del self.tilemap[loc]
        return matches



    # function to convert pixel position to grid position
    def tiles_around(self, pos):
        tiles = []
        # the double slash is integer/floor division, it'll chop off the remainder
        # for example 3/2 = 1.5 instead of getting 1.5 you'll get 1 in integer
        # why use this instead of just use division normal and then convert it into integer
        # Because integer truncates does not do proper integer conversion the same way that double slash does
        """Example 3 // 2 = 1
        int(3 / 2) = 1
        -3 // 2 = -2
        int(-3 / 2) = -1
        int(0.9) = 0
        int(-0.9) = 0 !!!!!!!!
        -9 // 10 = -1
        this is an important distinction
        you need to be very careful with converting things with computer graphics
        because if int(-0,9) = 0 then 2 or 3 pixel bordering 0 get brought into 1 or something
        , and it causes some issues """
        #           this is the X-axis position   and this is the Y-axis
        tile_loc = (int(pos[0] // self.tile_size), int(pos[1] // self.tile_size))
        for offset in NEIGHBOR_OFFSETS:
            # left to right X-axis and Y-axis
            check_loc = str(tile_loc[0] + offset[0]) + ';' + str(tile_loc[1] + offset[1])
            # Check if a tile is actually there because in a tile map there's alot of empty space
            if check_loc in self.tilemap:
                tiles.append(self.tilemap[check_loc])
        return tiles  # Return all the tiles around that location

    def save(self, path):
        f = open(path, 'w')
        json.dump({'tilemap': self.tilemap, 'tile_size': self.tile_size, 'offgrid': self.offgrid_tiles}, f)
        f.close()

    def load(self, path):
        f = open(path, 'r')
        map_data = json.load(f)
        f.close()

        self.tilemap = map_data['tilemap']
        self.tile_size = map_data['tile_size']
        self.offgrid_tiles = map_data['offgrid']

    def solid_check(self, pos):
        # convert pixel into the coordinate of the grid
        tile_loc = str(int(pos[0] // self.tile_size)) + ';' + str(int(pos[1] // self.tile_size))
        # if this location exists
        if tile_loc in self.tilemap:
            # if this is a physic tile (grass, stone)
            if self.tilemap[tile_loc]['type'] in PHYSIC_TILES:
                # then return that tile data
                # in our case we're not going to use the tile, just need to check if the tile exists
                return self.tilemap[tile_loc]

    def physics_rects_around(self, pos):
        rects = []  # rectangle that are going to be returned
        for tile in self.tiles_around(pos):  # Get all the nearby tiles
            if tile['type'] in PHYSIC_TILES:
                # pygame.rect(left, top, width, height)
                rects.append(
                    pygame.Rect(tile['pos'][0] * self.tile_size, tile['pos'][1] * self.tile_size, self.tile_size,
                                self.tile_size))
        return rects

    # function that auto put corresponding tile from current tile
    def autotile(self):
        for loc in self.tilemap:
            tile = self.tilemap[loc]
            neighbors = set()
            for shift in [(1, 0), (-1, 0), (0, -1), (0, 1)]:
                check_loc = str(tile['pos'][0] + shift[0]) + ';' + str(tile['pos'][1] + shift[1])
                if check_loc in self.tilemap:
                    # check if the neighbour tile is the same type as the tile itself
                    # if  not then don't auto tile
                    if self.tilemap[check_loc]['type'] == tile['type']:
                        neighbors.add(shift)
            neighbors = tuple(sorted(neighbors))
            if (tile['type'] in AUTOTILE_TYPES) and (neighbors in AUTOTILE_MAP):
                tile['variant'] = AUTOTILE_MAP[neighbors]

    def render(self, surf, offset=(0, 0)):
        # Off grid tile are mostly for decoration so put them before real tile
        # why do this is because you don't want to run into some decoration and get stopped by it
        """Off grid tile can be optimized too, you can learn about it if you interest in it"""
        for tile in self.offgrid_tiles:
            surf.blit(self.game.assets[tile['type']][tile['variant']],
                      (tile['pos'][0] - offset[0], tile['pos'][1] - offset[1]))

        """This loop iterates over a range of x and y coordinates that correspond to the visible area of the surface 
        (surf), adjusted by the camera offset (offset).
        The // operator performs floor division, 
        ensuring that the coordinates are aligned with the tile grid based on the self.tile_size."""
        for x in range(offset[0] // self.tile_size, (offset[0] + surf.get_width()) // self.tile_size + 1):
            for y in range(offset[1] // self.tile_size, (offset[1] + surf.get_height()) // self.tile_size + 1):
                """For each x and y coordinate pair, a string - representation of the coordinates - is created (loc) 
                to identify the tile's position in the tilemap.
                This string concatenation (str(x) + ';' + str(y)) creates a unique identifier 
                for each tile position, typically in the format "x;y"."""
                loc = str(x) + ';' + str(y)
                # check if loc exist in self.tilemap, ensuring a tile is defined for that position
                if loc in self.tilemap:
                    tile = self.tilemap[loc]
                    surf.blit(self.game.assets[tile['type']][tile['variant']],
                              (
                              tile['pos'][0] * self.tile_size - offset[0], tile['pos'][1] * self.tile_size - offset[1]))

        # These are tiles that you are going to run into
        # for loc in self.tilemap:
        #    tile = self.tilemap[loc]
        #    surf.blit(self.game.assets[tile['type']][tile['variant']],
        #              (tile['pos'][0] * self.tile_size - offset[0], tile['pos'][1] * self.tile_size - offset[1]))
