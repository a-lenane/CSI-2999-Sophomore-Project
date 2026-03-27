import pygame

class Player:

    def __init__(self,x,y,sprite):

        self.x = x
        self.y = y

        self.speed = 4

        self.sprite = pygame.transform.scale(sprite,(48,48))

        self.rect = pygame.Rect(x,y,48,48)

    def move(self,keys):

        if keys[pygame.K_w]:
            self.y -= self.speed
        if keys[pygame.K_s]:
            self.y += self.speed
        if keys[pygame.K_a]:
            self.x -= self.speed
        if keys[pygame.K_d]:
            self.x += self.speed

        self.rect.topleft = (self.x,self.y)

    def draw(self,screen,camera):

        screen.blit(
            self.sprite,
            (self.x-camera.x,self.y-camera.y)
        )