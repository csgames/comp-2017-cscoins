from .BaseCommand import BaseCommand
from Wallet import Wallet, generate_wallet_id
import hashlib

class CreateWalletCommand(BaseCommand):
    def __init__(self, central_authority_server):
        BaseCommand.__init__(self, central_authority_server, "create_wallet")
        self.database = self.central_authority_server.database

    def execute(self, response, client_connection, args):
        try:
            name = args['name']
            key = args['key']

            sha2 = hashlib.sha256()
            sha2.update(key.encode('ascii'))
            key = sha2.hexdigest()

            wallet_id = generate_wallet_id(name)
            w = Wallet(name, key, wallet_id)

            self.database.create_wallet(w)
            # self.central_authority_server.wallets.append(w)

            response['success'] = True
            response['wallet_id'] = wallet_id

            # generating aliases
            aliases = w.get_aliases(self.central_authority_server.aliases_per_wallet)
            self.database.add_wallet_aliases(w)
            self.database.add_wallet_balance(w)

            response['aliases'] = aliases

            print("New wallet created -> {0}".format(wallet_id))

        except Exception as e:
            print("{0} exception : {1}".format(self.__class__, e))
