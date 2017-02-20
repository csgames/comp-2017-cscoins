import decimal


class Transaction:
    def __init__(self, txn_dict=None):
        self.source = ""
        self.recipient = ""
        self.amount = decimal.Decimal(0.00000)
        self.id = 0

        if txn_dict is not None:
            self.__fill_from_dict(txn_dict)

    def __fill_from_dict(self, txn_dict):
        try:
            self.source = txn_dict["source"]
            self.recipient = txn_dict["recipient"]
            self.amount = decimal.Decimal(txn_dict["amount"])
            self.id = int(txn_dict["id"])

        except KeyError as e:
            print("Transaction.__fill_from_dict error : {0}".format(e))