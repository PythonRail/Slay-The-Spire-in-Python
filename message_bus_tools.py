from enum import StrEnum
from typing import Any
from ansi_tags import ansiprint
from definitions import Rarity, CardType, PlayerClass

class Message(StrEnum):
    '''Messages that can be sent to the message bus.'''
    START_OF_COMBAT = 'start_of_combat'
    END_OF_COMBAT = 'end_of_combat'
    START_OF_TURN = 'start_of_turn'
    END_OF_TURN = 'end_of_turn'
    BEFORE_ATTACK = 'before_attack'
    AFTER_ATTACK = 'after_attack'
    BEFORE_BLOCK = 'before_block'
    AFTER_BLOCK = 'after_block'
    ON_PICKUP = 'on_pickup' # For relics
    ON_DRAW = 'on_draw'
    ON_EXHAUST = 'on_exhaust'
    ON_CARD_PLAY = 'on_card_play'
    ON_CARD_ADD = 'on_card_add'

class MessageBus():
    '''This is a Pub/Sub, or Publish/Subscribe, message bus. It allows components to subscribe to messages,
    registering a callback function that will be called when that message is published.
    '''
    def __init__(self, debug=True):
        self.subscribers = dict(dict())
        self.debug = debug

    def subscribe(self, event_type: Message, callback, uid):
        if event_type not in self.subscribers:
            self.subscribers[event_type] = dict()
        self.subscribers[event_type][uid] = callback
        if self.debug:
            ansiprint(f"<basic>MESSAGEBUS</basic>: <blue>{event_type}</blue> | Subscribed <bold>{callback.__qualname__}</bold>")

    def publish(self, event_type: Message, data):
        if event_type in self.subscribers:
            for uid, callback in self.subscribers[event_type].items():
                if self.debug:
                    ansiprint(f"<basic>MESSAGEBUS</basic>: <blue>{event_type}</blue> | Calling <bold>{callback.__qualname__}</bold>")
                callback(event_type, data)
        return data
    
class Registerable():
    registers = []
    def register(self, bus):
        for message in self.registers:
            bus.subscribe(message, self.callback, self.uid)

class Effect(Registerable):
    def __init__(self, stack_type, info, amount=0):
        self.name = 'default'
        self.stack_type = stack_type
        self.info = info
        self.amount = amount

    def pretty_print(self):
        stack_type_colors = {'duration': 'light-blue', 'intensity': 'orange', 'counter': 'magenta', 'no stack': 'white'}
        return f"<{stack_type_colors[self.type]}>{self.name}</{stack_type_colors[self.type]}>{f' {self.amount}' if self.type != 'no stack' else ''}"

class Relic(Registerable):
    def __init__(self, name, info, flavor_text, rarity, player_class='Any'):
        self.name = name
        self.info = info
        self.flavor_text = flavor_text
        self.rarity = rarity
        self.player_class = player_class

    def pretty_print(self):
        return f"<{self.rarity}>{self.name}</{self.rarity}> | <yellow>{self.info}</yellow> | <italic><dark-blue>{self.flavor_text}</dark-blue></italic>"
    
class Card(Registerable):
    def __init__(self, name: str, info: str, rarity: Rarity, player_class: PlayerClass, card_type: CardType, target='Nothing', energy_cost=-1):
        self.name = name
        self.info = info
        self.rarity = rarity
        self.player_class = player_class
        self.type = card_type
        self.base_energy_cost = energy_cost
        self.energy_cost = energy_cost
        self.reset_energy_next_turn = False
        self.target = target
        self.upgrade = False
        self.upgrade_preview = f"{self.name} -> <green>{self.name + '+'}</green> | "

    def pretty_print(self):
        return f"""<{self.rarity.lower()}>{self.name}</{self.rarity.lower()}> | <light-black>{self.type}</light-black>{f' | <light-red>{"<green>" if self.base_energy_cost != self.energy_cost else ""}{self.energy_cost}{"</green>" if self.base_energy_cost != self.energy_cost else ""} Energy</light-red>' if self.energy > -1 else ''} | <yellow>{self.info}</yellow>"""

    def upgrade_markers(self):
        self.info += '<green>+</green>'
        self.upgraded = True
    
    def modify_energy_cost(self, amount, modify_type='Adjust', one_turn=False):
        if not (modify_type == 'Set' and amount != self.energy_cost) or not (modify_type == 'Adjust' and amount != 0):
            pass
        if modify_type == 'Adjust':
            self.energy_cost += amount
            ansiprint(f"{self.name} got its energy {'reduced' if amount < 0 else 'increased'} by {amount:+d}")
        elif modify_type == 'Set':
            self.energy_cost = amount
            ansiprint(f"{self.name} got its energy set to {amount}.")
        if one_turn:
            self.reset_energy_next_turn = True
bus = MessageBus(debug=True)