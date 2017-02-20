from .BaseCommand import BaseCommand
import random
import Transaction
import decimal
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5

class CreateTransactionCommand(BaseCommand):
    def __init__(self, central_authority_server):
        BaseCommand.__init__(self, central_authority_server, 'create_transaction')
        self.min_transaction_amount = self.central_authority_server.min_transaction_amount
        self.database = self.central_authority_server.database

    def execute(self, response, client_connection, args):
        try:
            source = args['source']
            recipient = args['recipient']
            amount = decimal.Decimal(args['amount'])
            signature = args['signature']
            sign_digest = bytes.fromhex(signature)
            source_wallet = self.database.get_wallet_by_id(source)
            recipient_wallet = self.database.get_wallet_by_id(recipient)

            if source_wallet is None:
                # invalid source
                remote_ip = client_connection.get_remote_ip()
                response["error"] = "Source and/or recipient wallet invalid"
                print("Invalid transaction (invalid source) tentative from ({0})".format(remote_ip))
                return

            signer = PKCS1_v1_5.new(RSA.importKey(source_wallet.key))
            # checking the signature
            message = "{0},{1},{2:.5f}".format(source, recipient, amount)
            hasher = SHA256.new()
            hasher.update(message.encode('ascii'))

            if not signer.verify(hasher, sign_digest):
                print("Invalid signature from {0}".format(source))
                response["error"] = "Invalid signature"
                return

            if recipient_wallet is None or source_wallet is None:
                # invalid recipient
                remote_ip = client_connection.get_remote_ip()
                response["error"] = "Source and/or recipient wallet invalid"
                print("Invalid transaction (invalid recipient) tentative from ({0})".format(remote_ip))
                return

            # amount is in balance or amount too low
            if source_wallet.balance < amount or amount < self.min_transaction_amount:
                remote_ip = client_connection.get_remote_ip()
                print("Invalid transaction (not enough funds) tentative from ({0})".format(remote_ip))
                response["error"] = "Not enough coins"
                return

            # Just in case...
            if recipient_wallet.id == source_wallet.id:
                remote_ip = client_connection.get_remote_ip()
                print("Invalid transaction (same wallet) tentative from ({0})".format(remote_ip))
                response["error"] = "Source and recipient are the same wallet"
                return

            # completing transaction
            source_wallet.balance -= amount
            recipient_wallet.balance += amount
            self.database.update_wallet_balance(source_wallet)
            self.database.update_wallet_balance(recipient_wallet)

            txn = Transaction.Transaction(0, source_wallet.id, recipient_wallet.id, amount)
            txn.signature = signature
            self.database.create_transaction(txn)
            response['id'] = txn.id

        except KeyError as e:
            response["error"] = "Missing argument(s)"
        except Exception as e:
            print("{0} exception : {1}".format(self.__class__, e))

