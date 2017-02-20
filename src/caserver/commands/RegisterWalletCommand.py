from .BaseCommand import BaseCommand
from Wallet import Wallet
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Signature import PKCS1_v1_5

class RegisterWalletCommand(BaseCommand):
    def __init__(self, central_authority_server):
        BaseCommand.__init__(self, central_authority_server, "register_wallet")
        self.database = self.central_authority_server.database

    def execute(self, response, client_connection, args):
        try:
            name = args['name']
            key = args['key']
            signature = args['signature']
            # generating Id from key
            pub_key = RSA.importKey(key)

            sha2 = SHA256.new()
            sha2.update(pub_key.exportKey(format='DER'))
            wallet_id = sha2.hexdigest()

            existing_wallet = self.database.get_wallet_by_id(wallet_id)

            if existing_wallet is not None:
                response["error"] = "Wallet {0} already registered"
                return

            # verifying the signature
            signer = PKCS1_v1_5.new(pub_key)
            sign_bytes = bytes.fromhex(signature)

            if not signer.verify(sha2, sign_bytes):
                print("Invalid Signature for Wallet Id {0}".format(wallet_id))
                response["error"] = "Invalid Signature"
                return

            w = Wallet(name, key, wallet_id)

            self.database.create_wallet(w)

            response['wallet_id'] = wallet_id

            self.database.add_wallet_balance(w)

            print("New wallet registered -> {0}".format(wallet_id))
        except KeyError as e:
            response["error"] = "Missing argument(s)"
        except Exception as e:
            print("{0} exception : {1}".format(self.__class__, e))