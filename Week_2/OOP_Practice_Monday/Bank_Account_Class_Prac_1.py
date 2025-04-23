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

'''
Research and summarize why OOP is beneficial for large projects.
Define a BankAccount class with attributes balance and methods deposit and withdraw.
Create a subclass SavingsAccount with an additional method add_interest.
'''

class BankAccount:
    def __init__(self, amount):
        self.amount = amount

    def deposit(self, dep_amount):
        self.amount = self.amount + dep_amount
        print(f'Current amount: {self.amount}')

    def withdrawal(self, with_amount):
        self.amount = self.amount - with_amount
        print(f'Current amount: {self.amount}')

class SavingsAccount(BankAccount):
    def __init__(self, amount):
        super().__init__(amount)

    def add_interest(self):
        interest = (self.amount * 0.10)
        self.amount += interest

    def __str__(self):
        return(f'Your new amount is... ${self.amount:.2f}')

Initial_Amount = SavingsAccount(200)
Initial_Amount.deposit(dep_amount=10)
Initial_Amount.withdrawal(with_amount=5)
Initial_Amount.add_interest()
print(Initial_Amount)