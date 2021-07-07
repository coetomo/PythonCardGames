import pygame
import pygame.display, pygame.image, pygame.transform, pygame.sprite, pygame.time, pygame.draw
import os, sys
import enum
from itertools import product
import random

CARD_IMG_PATH = "img/cards/"
BACK_CARD_IMG_FILE_PATH = "img/cards/back-side.png"

class State(enum.Enum):
    IDLE = 0
    DRAGGING = 1

class MouseClick(enum.Enum):
    NONE = 0
    LEFT = 1
    MIDD = 2
    RGHT = 3
    WHUP = 4
    WHDW = 5



class CardSprite(pygame.sprite.Sprite):
    def __init__(self, image, x, y, specSize, back_img):
        super().__init__()
        self.image = pygame.image.load(image).convert()
        self.back_img = pygame.image.load(back_img).convert()
        self.size = self.image.get_size()
        if specSize != None:
            if type(specSize) == float:
                new_size = (int(self.size[0]*specSize), 
                            int(self.size[1]*specSize))
                self.image = pygame.transform.scale(self.image, new_size)
                self.back_img = pygame.transform.scale(self.back_img, new_size)
            elif type(specSize) == tuple:     
                self.image = pygame.transform.scale(self.image, specSize)
                self.back_img = pygame.transform.scale(self.back_img, specSize)
        self.rect = self.image.get_rect(x=x, y=y)

    def move(self, x, y):
        self.rect.update((x, y), self.rect.size)

    def move_rel(self, rel):
        self.rect.move_ip(rel)

    def draw(self, surf):
        surf.blit(self.image, self.rect)
    
    def checkCollide(self, pos):
        return self.rect.collidepoint(pos)

    def flip(self):
        self.image, self.back_img = self.back_img, self.image
        

class Card():
    SUITS = ("S", "C", "H", "D")
    BLACKS = SUITS[:2]
    REDS = SUITS[2:]
    RANKS = tuple("A234567890JQK")
    JOKERS = ("ZB", "ZR")

    def __init__(self, cardstr, x=0, y=0, specSize=None, front_img=None, 
                    back_img=BACK_CARD_IMG_FILE_PATH):
        self.cardstr = cardstr
        if front_img is None:
            front_img = Card.img_path(cardstr)
        self.sprite = CardSprite(front_img, x, y, specSize, back_img)
        self.front = True

    def __str__(self) -> str:
        return f"<Card:{self.cardstr}>"

    @staticmethod
    def img_path(cardstr):
        path = CARD_IMG_PATH + cardstr + ".png"
        if os.path.exists(path):
            return path
        else:
            raise FileExistsError(f"{path} not found!")

    def move(self, x, y):
        self.sprite.move(x,y)

    def move_rel(self, rel):
        self.sprite.move_rel(rel)
    
    def draw(self, surf):
        self.sprite.draw(surf)

    def checkCollide(self, pos):
        return self.sprite.checkCollide(pos)

    def flip(self):
        self.sprite.flip()
        self.front = not self.front
    
    def facedown(self):
        if self.front:
            self.flip()

    def faceup(self):
        if not self.front:
            self.flip()


class CardHolder(list):
    def __init__(self, data=None):
        super().__init__()
        if data is not None:
            for elem in data:
                if not isinstance(elem, Card):
                    raise ValueError("Must be Card objects!")
                self.append(elem)

    def __str__(self):
        return f"<{self.__class__.__name__}:{[str(c) for c in self]}>"

    def __add__(self, other):
        if not issubclass(type(other), CardHolder):
            raise TypeError("Can only add using other CardHolder types!")
        return self.__init__(list(self) + list(other))
    
    def add_cards(self, other):
        if not issubclass(type(other), CardHolder):
            raise TypeError("Can only add using other CardHolder types!")
        for elem in other:
            if not isinstance(elem, Card):
                raise ValueError("Must be Card objects!")
            self.append(elem)
    
class Group(CardHolder):
    def __init__(self, x, y, dx, dy, size, data=None):
        super().__init__(data)
        self.x, self.y, self.dx, self.dy = x, y, dx, dy
        self.size = size
        self.update()
    
    def update(self):
        for i, card in enumerate(self):
            card.sprite.rect.update((self.x + i*self.dx, self.y + i*self.dy), self.size)

    def draw(self, surf):
        pygame.draw.rect(surf, pygame.Color(0, 0, 0), pygame.Rect(self.x-5, self.y-5, self.size[0]+100, self.size[1]+10), 3, 10)
        surf.blits([(c.sprite.image, c.sprite.rect) for c in self])
    
    def flip(self):
        for card in self:
            card.flip()
    # Needs to get its own file util or something
    # Also need some way to gurantee the order of cards when drawn
    def getFrontCard(self, pos):
        for i in range(len(self)-1, -1, -1):
            if self[i].checkCollide(pos):
                return (i, self[i])
        return None

class Pile(CardHolder):
    _BOTTOM_N_CARDS_DRAWN = 5

    def __init__(self, x, y, dx, dy, size, facedown=True, data=None):
        super().__init__(data)
        self.x, self.y, self.dx, self.dy = x, y, dx, dy
        self.size = size
        self.facedown = facedown
        self.update()

    def shuffle(self):
        random.shuffle(self)
        self.update()
    
    def update(self):
        for i, card in enumerate(self[:Pile._BOTTOM_N_CARDS_DRAWN]):
            card.facedown() if self.facedown else card.faceup()
            card.sprite.rect.update((self.x + i*self.dx, self.y + i*self.dy), self.size)

    def draw(self, surf):
        placeholders = self[:Pile._BOTTOM_N_CARDS_DRAWN]
        surf.blits([(c.sprite.image, c.sprite.rect) for c in placeholders])

    def checkCollide(self, pos):
        for card in self[:Pile._BOTTOM_N_CARDS_DRAWN]:
            if card.checkCollide(pos):
                return True
        return False

    def getTopCard(self):
        card = self.pop()
        if len(self) < Pile._BOTTOM_N_CARDS_DRAWN:
            self.update()
        return card


class Deck(Pile):
    _DEF_DX = 2
    _DEF_DY = 0

    def __init__(self, x, y, size, data=None):
        super().__init__(x, y, Deck._DEF_DX, Deck._DEF_DY, True, size, data)
    
    @staticmethod
    def standard(x, y, deckSize, cardSpecSize=1):
        cards = [Card(c, specSize=cardSpecSize) for c in list(product(Card.RANKS, Card.SUITS))]
        return Deck(x, y, deckSize, cards)
    
    @staticmethod
    def standard_plus(x, y, deckSize, add_cards, cardSpecSize=1):
        cards = [Card(c[0]+c[1], specSize=cardSpecSize) for c in list(product(Card.RANKS, Card.SUITS))]
        return Deck(x, y, deckSize, cards + add_cards)

    @staticmethod
    def standard_plus_jokers(x, y, deckSize, cardSpecSize=1):
        jokers = [Card(c, specSize=cardSpecSize) for c in Card.JOKERS]
        return Deck.standard_plus(x, y, deckSize, jokers, specSize=cardSpecSize)
    
    

def main():
    DISPLAY_SIZE = (800,600)
    GREEN=(0,128,0)
    CARD_SIZE = (100, 145)
    pygame.init()
    DISPLAY=pygame.display.set_mode(DISPLAY_SIZE)
    g = Group(10, 10, 18, 0, CARD_SIZE, [Card(s, specSize=CARD_SIZE) for s in ("4D", "5S", "6C", "QS", "JH", "8C")])

    clock = pygame.time.Clock()
    state = State.IDLE
    clicked = drag = topcard = None
    while True:
        
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if state == State.IDLE:
                    if event.button == MouseClick.LEFT.value:
                        state = State.DRAGGING
                        drag = g.getFrontCard(event.pos)
                    elif event.button == MouseClick.RGHT.value:
                        clicked = g.getFrontCard(event.pos)
                        #drawfromdeck = d.checkCollide(event.pos)
                        
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == MouseClick.LEFT.value:
                    if state == State.DRAGGING and drag:
                        g.pop(drag[0])
                        g.update()
                    drag = None
                    state = State.IDLE
                elif event.button == MouseClick.RGHT.value:
                    if clicked:
                        clicked[1].flip()
                        clicked = None
                    # elif drawfromdeck:
                    #     topcard = d.getTopCard()
                    #     print(topcard)
                    #     topcard.move(d.x + 150, d.y)
                    #     topcard.faceup()
                    #     topcard.draw(DISPLAY)
                    #     drawfromdeck = None
            elif event.type == pygame.MOUSEMOTION:
                if drag:
                    drag[1].move_rel(event.rel)
        
        DISPLAY.fill(GREEN)
        g.draw(DISPLAY)

        if topcard:
            topcard.draw(DISPLAY)
        pygame.display.flip()

        clock.tick(60)

main()