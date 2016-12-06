#!/usr/bin/python
import animats
import sys  # sys.exit()
import pygame
import json
import math


class Simulation:
    def __init__(self, num_herbivore, num_carnivore, num_trees, width, height, saved_nets):
        # initialize pygame
        pygame.init()

        # initialize the screen
        self.size = width, height
        self.screen = pygame.display.set_mode(self.size)
        self.screenWidth = width
        self.screenHeight = height

        # set the name of display windows
        pygame.display.set_caption('Import/Export project')

        # initialize sprites
        self.bg = pygame.image.load("./resources/bg.bmp")

        # pictures resources
        self.herbivore_spirit = pygame.image.load("./resources/animat.bmp")
        self.carnivore_spirit = pygame.image.load("./resources/carnivore.bmp")
        self.fruit = pygame.image.load("./resources/banana.bmp")
        self.tree = pygame.image.load("./resources/treepreview.bmp")


        # modify pictures to appropriate sizes
        self.herbivore_spirit = pygame.transform.scale(self.herbivore_spirit, (25, 25))
        self.carnivore_spirit = pygame.transform.scale(self.carnivore_spirit, (32, 32))
        self.bg = pygame.transform.scale(self.bg, (1000, 1000))
        self.fruit = pygame.transform.scale(self.fruit, (26, 26))
        self.tree = pygame.transform.scale(self.tree, (35, 35))

        self.env = animats.Environment(num_herbivore, num_carnivore, num_trees, width, height, saved_nets)

    def update(self, speed):
        # update model a certain number of times
        for i in range(speed):
            self.env.update()

        # for future 'pause' button, the parameter take milliseconds pause time
        # pygame.time.wait()

        # repaint
        self.screen.blit(self.bg, (0, 0))

        # paint food
        for food in list(filter(lambda fruit: isinstance(fruit, animats.Food), self.env.foods)):
            if isinstance(food, animats.Fruit):
                self.screen.blit(self.fruit, \
                                 (food.x - animats.Food.radius, \
                                  food.y - animats.Food.radius))
        for tree in list(self.env.trees):
            self.screen.blit(self.tree, \
                             (tree.x - animats.Trees.radius, \
                              tree.y - animats.Trees.radius))


        # paint animats
        for animat in self.env.animats:
            if isinstance(animat, animats.Herbivore):
                self.screen.blit(pygame.transform.rotate(self.herbivore_spirit, 360 - animat.direction),
                             (animat.x - animats.Animat.radius, animat.y - animats.Animat.radius))
            else:
                self.screen.blit(pygame.transform.rotate(self.carnivore_spirit, 360 - animat.direction),
                                 (animat.x - animats.Animat.radius, animat.y - animats.Animat.radius))
            if animat.food:
                if isinstance(animat.food, animats.Fruit):
                    self.screen.blit(self.fruit, \
                                     (animat.x - animats.Animat.radius, \
                                      animat.y - animats.Animat.radius))
                else:
                    self.screen.blit(self.herbivore_spirit, \
                                     (animat.x - animats.Animat.radius, \
                                      animat.y - animats.Animat.radius))
        # paint herbivore carcass
        for carcass in self.env.dead_herbivore:
            self.screen.blit(pygame.transform.rotate(self.herbivore_spirit, 360 - carcass.direction),
                             (carcass.x - animats.Animat.radius, carcass.y - animats.Animat.radius))

        pygame.display.flip()


def save_for_evaluation(simulation_obj, count_simulation):

    with open('age_generation_herbivore_dic.json', 'w') as f:
        json.dump(simulation_obj.env.age_generation_herbivore_dic, f)
    with open('age_generation_carnivore_dic.json', 'w') as f:
        json.dump(simulation_obj.env.age_generation_carnivore_dic, f)
    with open('carnivore_counts.json', 'w') as f:
        dictionary = {'count_simulation': count_simulation, 'mating_list': simulation_obj.env.mating_herbivore_list}
        json.dump(dictionary, f)
    with open('herbivore_counts.json', 'w') as f:
        dictionary = {'count_simulation':count_simulation, 'mating_list':simulation_obj.env.mating_herbivore_list}
        json.dump(dictionary, f)
    with open('herbivore_gene_inheritance.json','w') as f:
        json.dump(simulation_obj.env.herbivore_gene_inheritance, f)
    with open('carnivore_gene_inheritance.json', 'w') as f:
        json.dump(simulation_obj.env.carnivore_gene_inheritance, f)

if __name__ == "__main__":
    # load save state from file
    filename = ""
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    simulation = Simulation(5,5,5, 1000, 700, filename)
    count_simulation = 0
    # main loop
    while 1:
        for event in pygame.event.get():
            # check for exit
            if event.type == pygame.QUIT:
                simulation.env.save()
                save_for_evaluation(simulation, count_simulation)
                # save record log
                fLog = open("log.txt", 'w')
                map(lambda r: fLog.write(str(r) + '\n'), simulation.env.log)
                fLog.close()
                sys.exit()
        simulation.update(5)
        count_simulation += 1
