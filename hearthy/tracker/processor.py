import logging
from hearthy.tracker.world import World
from hearthy.protocol.utils import (
    TAG_CUSTOM_NAME, TAG_POWER_NAME, format_tag_name, format_tag_value
    )
from hearthy.tracker.entity import Entity
from pegasus.game_pb2 import PowerHistory

logger = logging.getLogger(__name__)

class Processor:
    def __init__(self):
        self._world = World()
        self.logger = logger

    def process(self, who, what):
        with self._world.transaction() as t:
            self._process(who, what, t)

    def _process(self, who, what, t):
        if isinstance(what, PowerHistory):
            for power in what.list:
                self._process_power(power, t)
        else:
            pass
            # self.logger.info('Ignoring packet of type {0}'.format(what.__class__.__name__))

    def _process_create_game(self, what, t):
        eid, taglist = (what.game_entity.id,
                        [(t.name, t.value) for t in what.game_entity.tags])
        if eid in t:
            # print('INFO: Game Entity already exists, ignoring "create game" event')
            return

        logging.info('Got game entity: {0}'.format(what.game_entity.id))
        logging.debug('With tags: \n' + '\n'.join(
            '\ttag {0}:{1} {2}'.format(tag_id, format_tag_name(tag_id),
                                      format_tag_value(tag_id, tag_val))
            for tag_id, tag_val in taglist))
        taglist.append((TAG_CUSTOM_NAME, 'TheGame'))
        t.add(Entity(eid, taglist))

        for player in what.players:
            eid, taglist = (player.entity.id,
                            [(t.name, t.value) for t in player.entity.tags])

            # TODO: are we interested in the battlenet id?
            logging.info('Found Player: {0}'.format(player.id))
            logging.debug('With tags: \n' + '\n'.join(
                '\ttag {0}:{1} {2}'.format(tag_id, format_tag_name(tag_id),
                                          format_tag_value(tag_id, tag_val))
                for tag_id, tag_val in taglist))

            taglist.append((TAG_CUSTOM_NAME, 'Player{0}'.format(player.id)))
            t.add(Entity(eid, taglist))

    def _process_power(self, power, t):
        if power.HasField('full_entity'):
            e = power.full_entity
            taglist = [(e.name, e.value) for e in e.tags]
            taglist.append((TAG_POWER_NAME, e.name))
            new_entity = Entity(e.entity, taglist)
            t.add(new_entity)

            # logging
            logger.info('Adding new entity: {0}'.format(new_entity))
            logger.debug('With tags: \n' + '\n'.join(
                '\ttag {0}:{1} {2}'.format(tag_id, format_tag_name(tag_id),
                                          format_tag_value(tag_id, tag_val))
                for tag_id, tag_val in taglist))
        if power.HasField('show_entity'):
            e = power.show_entity
            mut = t.get_mutable(e.entity)
            mut[TAG_POWER_NAME] = e.name

            for tag in e.tags:
                mut[tag.name] = tag.value

            logger.info('Revealing entity: {0}'.format(mut))
        if power.HasField('hide_entity'):
            pass
        if power.HasField('tag_change'):
            change = power.tag_change
            e = t.get_mutable(change.entity)

            logger.info('Tag change for {0}: {1} from {2} to {3}'.format(
                Entity.__str__(e),
                format_tag_name(change.tag),
                format_tag_value(change.tag, e[change.tag]) if e[change.tag] is not None else '(unset)',
                format_tag_value(change.tag, change.value)))

            e[change.tag] = change.value
        if power.HasField('create_game'):
            self._process_create_game(power.create_game, t)
        if power.HasField('power_start'):
            pass
        if power.HasField('power_end'):
            pass
        if power.HasField('meta_data'):
            pass
            # e = power.meta_data
            # logger.debug('{0}'.format(e))
