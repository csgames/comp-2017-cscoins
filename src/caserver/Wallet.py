import hashlib
import random
import time
import Transaction
import decimal


class Wallet(object):
    def __init__(self, name, key, id):
        self.nid = 0
        self.name = name
        self.key = key
        self.id = id
        self.balance = decimal.Decimal(0.00)

