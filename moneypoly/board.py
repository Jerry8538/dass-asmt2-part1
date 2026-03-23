"""deals with the game board"""

from moneypoly.property import Property, PropertyGroup, PropertyNumbers
from moneypoly.config import (
    JAIL_POSITION,
    GO_TO_JAIL_POSITION,
    FREE_PARKING_POSITION,
    INCOME_TAX_POSITION,
    LUXURY_TAX_POSITION,
)

# Maps fixed board positions to their tile type.
# Properties are looked up separately via get_property_at().
SPECIAL_TILES = {
    0: "go",
    JAIL_POSITION: "jail",
    GO_TO_JAIL_POSITION: "go_to_jail",
    FREE_PARKING_POSITION: "free_parking",
    INCOME_TAX_POSITION: "income_tax",
    LUXURY_TAX_POSITION: "luxury_tax",
    2:  "community_chest",
    17: "community_chest",
    33: "community_chest",
    7:  "chance",
    22: "chance",
    36: "chance",
    5:  "railroad",
    15: "railroad",
    25: "railroad",
    35: "railroad",
}


class Board:
    """Represents the MoneyPoly game board and all its tiles."""

    def __init__(self):
        self.groups = self._create_groups()
        self.properties = self._create_properties()

    def _create_groups(self):
        """Create and return the eight colour groups."""
        return {
            "brown":      PropertyGroup("Brown",      "brown"),
            "light_blue": PropertyGroup("Light Blue", "light_blue"),
            "pink":       PropertyGroup("Pink",       "pink"),
            "orange":     PropertyGroup("Orange",     "orange"),
            "red":        PropertyGroup("Red",        "red"),
            "yellow":     PropertyGroup("Yellow",     "yellow"),
            "green":      PropertyGroup("Green",      "green"),
            "dark_blue":  PropertyGroup("Dark Blue",  "dark_blue"),
            "railroad":   PropertyGroup("Railroad",   "railroad"),
        }

    def _create_properties(self):
        """Instantiate every purchasable property and return as a list."""
        g = self.groups
        return [
            Property("Mediterranean Avenue",   PropertyNumbers(1,  60,  2),  g["brown"]),
            Property("Baltic Avenue",          PropertyNumbers(3,  60,  4),  g["brown"]),
            Property("Oriental Avenue",        PropertyNumbers(6,  100, 6),  g["light_blue"]),
            Property("Vermont Avenue",         PropertyNumbers(8,  100, 6),  g["light_blue"]),
            Property("Connecticut Avenue",     PropertyNumbers(9,  120, 8),  g["light_blue"]),
            Property("St. Charles Place",      PropertyNumbers(11, 140, 10), g["pink"]),
            Property("States Avenue",          PropertyNumbers(13, 140, 10), g["pink"]),
            Property("Virginia Avenue",        PropertyNumbers(14, 160, 12), g["pink"]),
            Property("St. James Place",        PropertyNumbers(16, 180, 14), g["orange"]),
            Property("Tennessee Avenue",       PropertyNumbers(18, 180, 14), g["orange"]),
            Property("New York Avenue",        PropertyNumbers(19, 200, 16), g["orange"]),
            Property("Kentucky Avenue",        PropertyNumbers(21, 220, 18), g["red"]),
            Property("Indiana Avenue",         PropertyNumbers(23, 220, 18), g["red"]),
            Property("Illinois Avenue",        PropertyNumbers(24, 240, 20), g["red"]),
            Property("Atlantic Avenue",        PropertyNumbers(26, 260, 22), g["yellow"]),
            Property("Ventnor Avenue",         PropertyNumbers(27, 260, 22), g["yellow"]),
            Property("Marvin Gardens",         PropertyNumbers(29, 280, 24), g["yellow"]),
            Property("Pacific Avenue",         PropertyNumbers(31, 300, 26), g["green"]),
            Property("North Carolina Avenue",  PropertyNumbers(32, 300, 26), g["green"]),
            Property("Pennsylvania Avenue",    PropertyNumbers(34, 320, 28), g["green"]),
            Property("Park Place",             PropertyNumbers(37, 350, 35), g["dark_blue"]),
            Property("Boardwalk",              PropertyNumbers(39, 400, 50), g["dark_blue"]),
            Property("Reading Railroad",       PropertyNumbers(5,  200, 25), g["railroad"]),
            Property("Pennsylvania Railroad",  PropertyNumbers(15, 200, 25), g["railroad"]),
            Property("B. & O. Railroad",       PropertyNumbers(25, 200, 25), g["railroad"]),
            Property("Short Line",             PropertyNumbers(35, 200, 25), g["railroad"]),
        ]

    def get_property_at(self, position):
        """Return the Property at `position`, or None if there is none."""
        for prop in self.properties:
            if prop.numbers.position == position:
                return prop
        return None

    def get_tile_type(self, position):
        """
        Return a string describing the tile at `position`.
        Possible values: 'go', 'jail', 'go_to_jail', 'free_parking',
        'income_tax', 'luxury_tax', 'community_chest', 'chance',
        'railroad', 'property', 'blank'.
        """
        if position in SPECIAL_TILES:
            return SPECIAL_TILES[position]
        if self.get_property_at(position) is not None:
            return "property"
        return "blank"

    def is_purchasable(self, position):
        """
        Return True if the tile at `position` is a property that can be bought.
        Mortgaged properties are not considered purchasable.
        """
        prop = self.get_property_at(position)
        if prop is None:
            return False
        if prop.is_mortgaged:
            return False
        return prop.owner is None

    def is_special_tile(self, position):
        """Return True if `position` holds a non-property special tile."""
        return position in SPECIAL_TILES

    def properties_owned_by(self, player):
        """Return a list of all properties currently owned by `player`."""
        return [p for p in self.properties if p.owner == player]

    def unowned_properties(self):
        """Return a list of all properties that have not yet been purchased."""
        return [p for p in self.properties if p.owner is None]

    def __repr__(self):
        owned = sum(1 for p in self.properties if p.owner is not None)
        return f"Board({len(self.properties)} properties, {owned} owned)"
