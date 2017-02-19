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
            # validate submission right away
            challenge_id = int(args['challenge_id'])
            nonce = int(args['nonce'])
            hash = args['hash']
            wallet_id = args['wallet_id']
            signature = args['signature']

            # todo
            # verifying the signature first
            message = "{0},{1},{2}".format(challenge_id, nonce, hash)
            hasher = SHA256.new()
            hasher.update(message.encode('ascii'))

            wallet = self.database.get_wallet_by_id(wallet_id)

            if wallet is None:
                return

            try:
                wallet_key = RSA.importKey(wallet.key)
                signer = PKCS1_v1_5.new(wallet_key)
                if not signer.verify(hasher, bytes.fromhex(signature)):
                    print("Signature invalid for Wallet : {0}".format(wallet_id))
                    return
            except:
                print("Wallet {0} isn't registered".format(wallet_id))
                return

            current_challenge = self.database.get_current_challenge()
            print("Submission accepted for Wallet {0}".format(wallet.id))
            if current_challenge.id == challenge_id:
                submission = Submission(challenge_id, nonce, hash, wallet)
                self.database.add_or_update_submission(submission)
                response['success'] = True
                response['submission_id'] = submission.id

        except Exception as e:
            print("{0} exception : {1}".format(self.__class__, e))