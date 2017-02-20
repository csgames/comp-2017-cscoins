from .BaseCommand import BaseCommand
from caserver.challenges import Submission
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Signature import PKCS1_v1_5
import base64

class SubmissionCommand(BaseCommand):
    def __init__(self, central_authority_server):
        BaseCommand.__init__(self, central_authority_server, "submission")
        self.database = self.central_authority_server.database

    def execute(self, response, client_connection, args):
        remote_ip = client_connection.get_remote_ip()
        if not self.central_authority_server.is_ip_allowed_to_submit(remote_ip):
            print("{0} is not allowed to do submission".format(remote_ip))
            return

        try:
            nonce = int(args['nonce'])
            wallet_id = args['wallet_id']

            wallet = self.database.get_wallet_by_id(wallet_id)

            if wallet is None:
                response["error"] = "Unregistered wallet"
                return

            current_challenge = self.database.get_current_challenge()
            print("Submission accepted for Wallet {0}".format(wallet.id))
            submission = Submission(current_challenge.id, nonce, wallet)
            self.database.add_or_update_submission(submission)

        except KeyError as e:
            response["error"] = "Missing argument(s)"
        except Exception as e:
            print("{0} exception : {1}".format(self.__class__, e))