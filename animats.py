# Animats environment model
import pickle
import random
import math
from pybrain.structure import FeedForwardNetwork, LinearLayer, SigmoidLayer, FullConnection
import collections


# Environment which contains animats and foods
class Environment:
    def __init__(self, num_herbivore, num_carnivore, num_trees, width, height, filename):
        # Training Mode.
        self.training_mode = True
        # Environment
        self.width = width
        self.height = height
        # record log
        self.log = []
        self.moveLog = []
        # save state
        self.filename = filename
        # foods
        num_animats = num_herbivore + num_carnivore
        self.num_foods = num_animats
        self.foods = []
        self.produceFoods
        # animats
        self.herbivore = []
        self.carnivore = []
        self.num_herbivores = num_herbivore
        self.num_carnivore = num_carnivore
        self.num_animats = num_animats
        self.deaths = []
        self.animats = []
        self.dead_herbivore = []
        # Trees for caching herbivore carcass
        self.num_trees = num_trees
        self.trees = []
        # Experiment results for visualization purposes.
        self.age_generation_herbivore_dic = collections.defaultdict(list)
        self.age_generation_carnivore_dic = collections.defaultdict(list)
        self.mating_herbivore_count = 0
        self.mating_herbivore_list = []
        self.mating_carnivore_count = 0
        self.mating_carnivore_list = []
        self.herbivore_gene_inheritance = collections.defaultdict(list)
        self.carnivore_gene_inheritance = collections.defaultdict(list)
        saved_states = self.load()
        while len(self.herbivore) < num_herbivore:
            pos = self.findSpace(Animat.radius, (0, self.height))
            if len(saved_states) > 0:
                a = saved_states.pop(0)
                a.x = pos[0]
                a.y = pos[1]
            else:
                a = Herbivore(pos[0], pos[1], random.random() * 360)
                a.generation = 0
            self.herbivore.append(a)
            self.animats.append(a)
            self.foods.append(a)

        while len(self.carnivore) < num_carnivore:
            pos = self.findSpace(Animat.radius, (0, self.height))
            if len(saved_states) > 0:
                a = saved_states.pop(0)
                a.x = pos[0]
                a.y = pos[1]
            else:
                a = Carnivore(pos[0], pos[1], random.random() * 360)
                a.generation = 0
            self.carnivore.append(a)
            self.animats.append(a)

    # animat line of sight
    def line_of_sight(self, animat):
        step_x = int(math.cos(animat.direction * math.pi / 180) * 10)
        step_y = int(math.sin(animat.direction * math.pi / 180) * 10)
        new_x = animat.x + step_x
        new_y = animat.y + step_y
        sees = None
        while not sees:
            new_x += step_x
            new_y += step_y
            sees = self.collision(new_x, new_y, Animat.radius, animat)
        return sees

    def collision(self, x, y, radius, without=None):
        # check wall collision
        if (y + radius) > self.height or (x + radius) > self.width \
                or (x - radius) < 0 or (y - radius) < 0:
            return self
        # check animat-animat collision
        animats = list(self.animats)
        if without:
            animats.remove(without)
        for animat in animats:
            if (x - animat.x) ** 2 + (y - animat.y) ** 2 <= Animat.radius ** 2:
                return animat
        # check collision with food(fruit)
        fruits = list(self.foods)
        if isinstance(without, Herbivore):
            fruits.remove(without)
        for fruit in fruits:
            if (x - fruit.x) ** 2 + (y - fruit.y) ** 2 <= Animat.radius ** 2:
                return fruit
        # check collision with trees
        trees = list(self.trees)
        for tree in trees:
            if (x - tree.x) ** 2 + (y - tree.y) ** 2 <= Animat.radius ** 2:
                if tree.carcass:
                    print("Returning tree carcass {0}".format(tree.carcass))
                    return tree.carcass
                else:
                    return tree
        # check collision with carcass
        carcasses = list(self.dead_herbivore)
        for carcass in carcasses:
            if (x - tree.x) ** 2 + (y - tree.y) ** 2 <= Animat.radius ** 2:
                print("Returning Carcass {0}".format(carcass))
                return carcass
        # no collision
        return None

    # find a random spot to spawn animats
    def findSpace(self, radius, bounds):
        spawns_x = list(range(0, self.width, 10))
        spawns_y = list(range(int(bounds[0]), int(bounds[1]), 10))
        random.shuffle(spawns_x)
        random.shuffle(spawns_y)
        for x in spawns_x:
            for y in spawns_y:
                if not self.collision(x, y, radius):
                    return (x, y)

    def growTrees(self, train=False):
        trees_bounds = (0, self.height / 3)
        if train:
            trees_bounds = (0, self.height)
        while len(list(self.trees)) < self.num_trees:
            pos = self.findSpace(Trees.radius, trees_bounds)
            self.trees.append(Trees(pos[0], pos[1]))

    # return the amount of food in the environment to a fixed state
    def produceFoods(self, train=False):
        fruit_bounds = (0, self.height / 7)
        herbivore_bounds = (0, self.height / 3)
        if self.training_mode:
            fruit_bounds = (0, self.height)
        while len(list(filter(lambda f: isinstance(f, Fruit), self.foods))) < self.num_foods:
            pos = self.findSpace(Food.radius, fruit_bounds)
            self.foods.append(Fruit(pos[0], pos[1]))
        while len(list(filter(lambda animat: isinstance(animat, Herbivore), self.animats))) < self.num_herbivores:
            pos = self.findSpace(Animat.radius, herbivore_bounds)
            herbivore = Herbivore(pos[0], pos[1], random.random() * 360)
            self.herbivore.append(herbivore)
            self.animats.append(herbivore)
            self.foods.append(herbivore)

    def isFreeTree(self, tree):
        return True if not tree.carcass else False

    def update(self):
        # if an animat died, the two fittest animats mate
        herbivore = list(filter(lambda animat: isinstance(animat, Herbivore), self.deaths))
        while len(herbivore) > 0:
            fittest = sorted(self.herbivore, key=lambda a: -a.avg_fruit_hunger)
            pos = self.findSpace(Animat.radius, (0, self.height))
            child, herbivore_gene_inheritance = fittest[0].mate(fittest[1])
            self.mating_herbivore_count += 1
            self.mating_herbivore_list.append(self.mating_herbivore_count)
            self.herbivore_gene_inheritance[child.generation].append(herbivore_gene_inheritance)
            child.x = pos[0]
            child.y = pos[1]
            self.animats.append(child)
            self.herbivore.append(child)
            self.foods.append(child)
            popped = herbivore.pop(0)
            self.animats.remove(popped)
            self.herbivore.remove(popped)
            self.deaths.remove(popped)
            death_and_mating = [popped, fittest[0], fittest[1], child]
            print("Death : {0}, Mating : {1} and {2}, Child: {3}".format(*death_and_mating))
        carnivore = list(filter(lambda animat: isinstance(animat, Carnivore), self.deaths))
        while len(carnivore) > 0:
            fittest = sorted(self.carnivore, key=lambda a: -a.avg_herbivore_hunger)
            pos = self.findSpace(Animat.radius, (0, self.height))
            child, carnivore_gene_inheritance = fittest[0].mate(fittest[1])
            self.mating_carnivore_count += 1
            self.mating_carnivore_list.append(self.mating_carnivore_count)
            self.carnivore_gene_inheritance[child.generation].append(carnivore_gene_inheritance)
            child.x = pos[0]
            child.y = pos[1]
            self.animats.append(child)
            self.carnivore.append(child)
            popped = carnivore.pop(0)
            self.animats.remove(popped)
            self.carnivore.remove(popped)
            self.deaths.remove(popped)
            death_and_mating = [popped, fittest[0], fittest[1], child]
            print("Death : {0}, Mating : {1} and {2}, Child: {3}".format(*death_and_mating))
        animat_touching_dic = {}

        for animat in self.animats:
            # update sensory information from environment
            animat.sees = self.line_of_sight(animat)
            step = 3
            step_x = int(math.cos(animat.direction * math.pi / 180) * step)
            step_y = int(math.sin(animat.direction * math.pi / 180) * step)
            animat.touching = self.collision(animat.x + step_x, animat.y + step_y, Animat.radius, animat)
            animat_touching_dic[animat] = animat.touching
            # update animat response to environment
            animat.update()
            if isinstance(animat, Herbivore):
                self.age_generation_herbivore_dic[animat.generation].append(animat.age)
            elif isinstance(animat, Carnivore):
                self.age_generation_carnivore_dic[animat.generation].append(animat.age)
            # perform animat decided action in environment
            if animat.wants_to_move:
                if (not animat.touching or (isinstance(animat, Herbivore) and isinstance(animat.touching, Food))
                    or (isinstance(animat, Carnivore) and isinstance(animat.touching, Herbivore))):
                    animat.x += step_x
                    animat.y += step_y
            if isinstance(animat, Herbivore) and isinstance(animat.touching, Food) and animat.wants_to_pickup:
                self.foods.remove(animat.touching)
                animat.food = animat.touching
            if isinstance(animat, Carnivore) and isinstance(animat.touching, Herbivore) and animat.wants_to_pickup:
                try:
                    self.animats.remove(animat.touching)
                    self.herbivore.remove(animat.touching)
                    self.foods.remove(animat.touching)
                    animat.food = animat.touching
                except ValueError:
                    pass
                finally:
                    # print("Touching : {0}, Animat : {1}".format(animat.touching, animat))
                    if animat.carcass:
                        empty_trees = list(filter(lambda tree: self.isFreeTree(tree), self.trees))
                        if empty_trees:
                            tree = empty_trees[random.randint(0,len(empty_trees)-1)]
                            animat.touching.x, animat.touching.y = tree.x, tree.y
                            print("Caching herbivore {0} in the tree {1}".format(animat.touching,tree))
                            self.dead_herbivore.append(animat.touching)
                            print("Cached Dead Herbivore : ", self.dead_herbivore)
                            self.trees[self.trees.index(tree)].carcass = animat.touching
            if isinstance(animat, Carnivore) and animat.wants_to_eat_cache:
                animat.sees = self.line_of_sight(animat)
                if isinstance(animat.sees, Herbivore) and animat.sees in self.dead_herbivore:
                    self.dead_herbivore.remove(animat.sees)
                    print("Carnivore {0} ate cached {1} {2}".format(animat, animat.sees.__class__,  animat.sees))

            if animat.wants_to_putdown:
                if isinstance(animat.food, Fruit):
                    self.foods.append(Fruit(animat.x - (step_x * 10), animat.y - (step_y * 10)))
                elif isinstance(animat.food, Herbivore):
                    self.foods.append(
                        Herbivore(animat.x - (step_x * 10), animat.y - (step_y * 10), random.random() * 360))
                animat.food = None


            # control the amount of food and animats in the environment
            self.produceFoods()
            self.growTrees()
            if animat not in self.deaths \
                    and ((isinstance(animat, Herbivore) and animat.fruit_hunger < 1000) or (
                        isinstance(animat, Carnivore) and animat.herbivore_hunger < 1000)):
                self.deaths.append(animat)
                # print("Touching Dictionary : ", animat_touching_dic)

    # load saved animat states into environment
    def load(self):
        if self.filename == "":
            return []
        try:
            f = open(self.filename, 'r')
            animats = pickle.load(f)
            f.close()
            return animats
        except:
            # print "Could not load file " + self.filename
            return []

    def save(self):
        if self.filename != "":
            f = open(self.filename, 'w')
            pickle.dump(self.animats, f)
            f.close()


# Animats
class Animat:
    radius = 40

    def __init__(self, x, y, direction):
        self.age = 0
        # position
        self.x = x
        self.y = y
        # number of going back and forth for different foods
        self.backForth = 0

        # orientation (0 - 359 degrees)
        self.direction = direction
        # carrying food
        self.food = None
        # touching anything
        self.touching = None
        self.sees = None
        # hunger sensor
        self.fruit_hunger = 2000
        self.herbivore_hunger = 2000

        self.avg_fruit_hunger = 0
        self.avg_herbivore_hunger = 0

        self.generation = 0
        # neural net
        self.net = FeedForwardNetwork()
        if isinstance(self, Carnivore):
            self.net.addInputModule(LinearLayer(9, name='in'))
        else:
            self.net.addInputModule(LinearLayer(8, name='in'))
        self.net.addModule(SigmoidLayer(13, name='hidden1'))
        if isinstance(self, Carnivore):
            self.net.addOutputModule(LinearLayer(7, name='out'))
        else:
            self.net.addOutputModule(LinearLayer(6, name='out'))
        self.net.addConnection(FullConnection(self.net['in'], self.net['hidden1']))
        self.net.addConnection(FullConnection(self.net['hidden1'], self.net['out']))
        self.net.sortModules()
        # thresholds for deciding an action
        self.move_threshold = 0
        self.pickup_threshold = 0
        self.putdown_threshold = 0
        self.cache_eat_threshold = 0
        self.eat_threshold = -10
        self.caching_threshold = [1500,1800]
        self.wants_to_move = True
        self.carcass = None

        # For visualization purposes
        self.choice_gene_inheritance = collections.defaultdict(list)

    def update(self):
        if isinstance(self, Herbivore):
            sensors = [2000 * int(isinstance(self.sees, Fruit) or \
                                  (isinstance(self.sees, Animat) and \
                                   isinstance(self.sees.food, Fruit))),
                       2000 * int(isinstance(self.sees, Animat)),
                       2000 * int(isinstance(self.sees, Environment)),
                       2000 * int(isinstance(self.food, Fruit)),
                       self.fruit_hunger,
                       2000 * int(isinstance(self.touching, Fruit) or \
                                  (isinstance(self.touching, Animat) and \
                                   isinstance(self.touching.food, Fruit))),
                       2000 * int(isinstance(self.touching, Animat)),
                       2000 * int(isinstance(self.touching, Environment))]
        elif isinstance(self, Carnivore):
            sensors = [2000 * int(isinstance(self.sees, Herbivore) or (isinstance(self.sees, Fruit)) or (
                isinstance(self.sees, Carnivore) and (isinstance(self.sees.food, Herbivore)))),
                       2000 * int(isinstance(self.sees, Animat)),
                       2000 * int(isinstance(self.sees, Environment)),
                       2000 * int(isinstance(self.food, Herbivore)),
                       self.herbivore_hunger,
                       2000 * int(isinstance(self.touching, Herbivore) or \
                                  (isinstance(self.touching, Herbivore) and \
                                   isinstance(self.touching.food, Herbivore))),
                       2000 * int(isinstance(self.touching, Animat)),
                       2000 * int(isinstance(self.touching, Environment)),
                       2000*int(isinstance(self.touching, Herbivore) and 1200 >= self.herbivore_hunger >= 1000)]
        decision = self.net.activate(sensors)
        if isinstance(self, Carnivore):
            print("Sensors are : ", decision)
        self.age += 1
        self.get_hungry(0.5)

        # move forward
        self.wants_to_move = (decision[0] >= self.move_threshold)

        # rotate left
        self.direction -= decision[1]

        # rotate right
        self.direction += decision[2]

        # pickup
        self.wants_to_pickup = ((decision[3] > self.pickup_threshold)
                                and not self.food)
        # putdown
        self.wants_to_putdown = ((decision[4] > self.putdown_threshold)
                                 and self.food)
        if isinstance(self, Carnivore):
            self.wants_to_eat_cache = ((decision[6] > self.cache_eat_threshold) and
                                       not self.touching and self.wants_to_pickup)

        # eat

        if (decision[5] > self.eat_threshold) and self.food:
            if isinstance(self, Herbivore) and isinstance(self.food, Fruit):
                print("entered for herbivore and eating food. with hunger: ", self.fruit_hunger)
                self.fruit_hunger = 2000 if (self.fruit_hunger > 1800) else (self.fruit_hunger + 200)
                self.avg_fruit_hunger = (self.avg_fruit_hunger + self.fruit_hunger) / 2
            elif isinstance(self, Carnivore) and isinstance(self.food, Herbivore):
                print("entered for carnivore and eating food. with hunger: ", self.herbivore_hunger)
                if self.caching_threshold[1] > self.herbivore_hunger > self.caching_threshold[0]:
                    print("entered for carnivore and caching food with hunger: ", self.herbivore_hunger)
                    self.carcass = self.food
                else:
                    self.herbivore_hunger = 2000 if (self.herbivore_hunger > 1800) else (self.herbivore_hunger + 200)

                self.avg_herbivore_hunger = (self.herbivore_hunger + self.herbivore_hunger) / 2
            self.food = None

    def get_hungry(self, amount):
        self.fruit_hunger -= amount
        self.herbivore_hunger -= amount

    # returns a child with a genetic combination of neural net weights of 2 parents (mating is done within same species)
    def mate(self, other):
        if isinstance(self, Carnivore):
            child = Carnivore(0, 0, random.random() * 360)
        else:
            child = Herbivore(0, 0, random.random() * 360)
        child.generation = min(self.generation, other.generation) + 1
        # inherit parents connection weights
        fittest_choice_counter = 0
        second_fittest_choice_counter = 0
        for i in range(0, len(self.net.params)):
            if random.random() > .1:
                choice = random.choice([0,1])
                if choice ==0:
                    child.net.params[i] = self.net.params[i]
                    fittest_choice_counter += 1
                elif choice == 1:
                    child.net.params[i] = other.net.params[i]
                    second_fittest_choice_counter += 1

        return child, [fittest_choice_counter/len(self.net.params), second_fittest_choice_counter/len(self.net.params)]


class Food:
    radius = 30

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.bites = 10


class Trees:
    radius = 30

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.carcass = None


class Fruit(Food):
    pass


class Herbivore(Animat):
    pass


class Carnivore(Animat):
    pass


class Carcass(Herbivore):
    pass
