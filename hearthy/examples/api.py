from hearthy import exceptions
from hearthy.tracker.entity import Entity
from hearthy.protocol.utils import format_tag_name

HERO1 = 64
HERO1_SKILL = 65
HERO2 = 66
HERO2_SKILL = 67

class HearthyAPI:

    wd = {}
    """Implement API of Hearthy."""

    def __init__(self, world):
        """Load one world. """
        if HERO2_SKILL not in world:
            raise exceptions.EntityNotFound(HERO2_SKILL)
        self.wd = world

    def get_player(self, opponent):
        """Return a player status.
        :opponent: boolean, if False return self otherwise return opponent
        :returns: player dict
        """
        my_hero = self.wd[HERO1]
        my_skill = self.wd[HERO1_SKILL]
        opponent_hero = self.wd[HERO2]
        opponent_skill = self.wd[HERO2_SKILL]
        if opponent:
            hero = opponent_hero
            skill = opponent_skill
        else:
            hero = my_hero
            skill = my_skill
        ret = entity2dict(hero)
        ret['skill'] = entity2dict(skill)
        return ret

    @staticmethod
    def entity2dict(e):
        """Convert all tags of entity to dict with tag_name.

        :entitiy: entity-like object (e.g.: a dict with some tag is ok)
        :returns: dict{'_raw': raw dict, tag_name: tag_value}

        """
        ret = {}
        ret['_raw'] = e
        try:
            for tag, v in e.items():
                ret[format_tag_name(tag)] = v
        except TypeError as e:
            print(type(e), "is not iterable")
            return ret

