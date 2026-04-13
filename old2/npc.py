import pygame
import random

class NPC:

    def __init__(self,x,y,sprite):

        self.x = x
        self.y = y

        self.sprite = pygame.transform.scale(sprite,(48,48))

        self.timer = 0
        self.direction = (0,0)

    def update(self):

        self.timer -= 1

        if self.timer <= 0:

            self.direction = random.choice([
                (1,0),(-1,0),(0,1),(0,-1),(0,0)
            ])

            self.timer = random.randint(40,120)

        self.x += self.direction[0]*2
        self.y += self.direction[1]*2

    def draw(self,screen,camera):

        screen.blit(
            self.sprite,
            (self.x-camera.x,self.y-camera.y)
        )