from enum import Enum

# customer difficulty levels
class Customer_Type(Enum):
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"


class Session:
    def __init__(self, description, personality, customer_type, interest_level):
        self.counter = 0
        self.history = []
        self.description = description
        self.personality = personality
        self.customer_type = customer_type
        self.objections = []
        self.interest_level = interest_level

    def update_counter(self):
        self.counter += 1

    def update_interest_level(self, increase):
        if (increase):
            if (self.interest_level < 5):
                self.interest_level += 1
            
        else:
            if (self.interest_level > 1):
                self.interest_level -= 1

        

    