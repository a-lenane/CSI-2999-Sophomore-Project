class Camera:

    def __init__(self):
        self.x = 0
        self.y = 0

    def update(self,player):

        self.x = player.x - 450
        self.y = player.y - 300