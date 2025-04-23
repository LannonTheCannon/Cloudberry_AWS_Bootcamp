'''
Homework:
Design a Vehicle class with subclasses Car and Bike, each with unique attributes and behaviors.
'''

class vehicle():
    def __init__(self, name, brand, model):
        self.name = name
        self.brand = brand
        self.model = model

    def vroom(self):
        print('vroom vroom')

class Car(vehicle):
    def __init__(self, name, brand, model, num_cylinders):
        super().__init__(name, brand, model)
        self.num_cylinders = num_cylinders

    def vroom(self):
        print(f'{self.name} car go fast with {self.num_cylinders} cylinders!')

class Bike(vehicle):
    def vroom(self):
        print(f'{self.name} bike go fast')

badboy_1 = vehicle('Tiff', 'Mercedes', 'S550')
badboy_2 = vehicle('Max', 'Nissan',"GTR R35")

print(badboy_1.name)
badboy_2.vroom()