import websockets
import json
import ssl
from .Transaction import Transaction
from .Challenge import Challenge
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto import Random
from Crypto.Signature import PKCS1_v1_5


class BaseClient:
    def __init__(self, hostname="localhost", port=8989, ssl=True):
        self.hostname = hostname
        self.port = port
        self.ssl = ssl
        self.socket = None

        self.public_key = None
        self.private_key = None
        self.wallet_id = ""
        self.wallet_name = ""

    def sign_message(self, digest):
        signer = PKCS1_v1_5.new(self.private_key)
        sign_bytes = signer.sign(digest)
        signature = ""
        for b in sign_bytes:
            signature += "{0:02x}".format(b)
        return signature

    def generate_wallet_keys(self):
        prng = Random.new().read
        self.private_key = RSA.generate(1024, prng)
        self.public_key = self.private_key.publickey()

    def load_keys(self, public_key_path, private_key_path):
        fp = open(public_key_path, 'rb')
        self.public_key = RSA.importKey(fp.read(4096))
        fp.close()

        fp = open(private_key_path, 'rb')
        self.private_key = RSA.importKey(fp.read(4096))
        fp.close()

    def export_keys(self, public_key_path, private_key_path, format='PEM'):
        fp = open(public_key_path, 'wb')
        fp.write(self.public_key.exportKey(format=format))
        fp.close()

        fp = open(private_key_path, 'wb')
        fp.write(self.private_key.exportKey(format=format))
        fp.close()

    def generate_wallet_id(self):
        hasher = SHA256.new()
        hasher.update(self.public_key.exportKey(format='DER'))
        self.wallet_id = hasher.hexdigest()

    async def connect(self):
        if self.ssl:
            ssl_context = ssl.SSLContext(protocol=ssl.PROTOCOL_SSLv23)
            self.socket = await websockets.client.connect("wss://{0}:{1}/client".format(self.hostname, self.port), ssl=ssl_context)
        else:
            self.socket = await websockets.client.connect("ws://{0}:{1}/client".format(self.hostname, self.port))

    async def submit(self, nonce):

        command = {
            'command': 'submission',
            'args': {
                'nonce': nonce,
                'wallet_id': self.wallet_id}}
        message = json.dumps(command)
        await self.socket.send(message)

        message = await self.socket.recv()
        response = json.loads(message)

        print("Submission result: {0}".format(response))

        if 'error' in response:
            print("Error during submission : {0}".format(response["error"]))

        if 'challenge_name' in response:
            # we got a new challenge
            challenge = Challenge()
            challenge.fill_from_challenge(response)

            return challenge
        return None

    async def get_challenge_solution(self, challenge_id):
        command = {'command': 'get_challenge_solution',
                   'args': {'challenge_id': challenge_id}}
        message = json.dumps(command)
        await self.socket.send(message)

        message = await self.socket.recv()
        data = json.loads(message)

        return data

    async def get_current_challenge(self):
        command = {'command': 'get_current_challenge', 'args': {}}
        message = json.dumps(command)
        await self.socket.send(message)

        message = await self.socket.recv()
        data = json.loads(message)
        return data

    async def get_transactions(self, start=0, count=100):
        command = {
            'command': 'get_transactions',
            'args': {
                'start': start,
                'count': count}}
        message = json.dumps(command)
        await self.socket.send(message)

        message = await self.socket.recv()
        data = json.loads(message)

        transactions = []

        if data['success']:
            for txn in data['transactions']:
                t = Transaction(txn)
                if t.id > 0:
                    transactions.append(t)

        return transactions

    async def create_transaction(self, recipient, amount):
        hasher = SHA256.new()
        hasher.update(
            "{0},{1},{2:.5f}".format(
                self.wallet_id,
                recipient,
                amount))
        signature = self.sign_message(hasher)
        command = {
            'command': 'create_transaction',
            'args': {
                'source': self.wallet_id,
                'recipient': recipient,
                'amount': "{0:.5f}".format(amount),
                signature: signature}}
        message = json.dumps(command)
        await self.socket.send(message)

        message = await self.socket.recv()
        response = json.loads(message)

        if 'error' in response:
            print(
                "Error during create_transaction : {0}".format(
                    response['error']))

        if 'id' in response:
            return response['id']

        return None

    async def register_wallet(self):
        # create the wallet
        keyString = ""
        for b in self.public_key.exportKey(format='PEM'):
            keyString += chr(b)

        hasher = SHA256.new()
        hasher.update(self.public_key.exportKey(format='DER'))
        signature = self.sign_message(hasher)

        command = {
            "command": "register_wallet",
            "args": {
                "name": self.wallet_name,
                "key": keyString,
                "signature": signature}}
        message = json.dumps(command)
        await self.socket.send(message)
        message = await self.socket.recv()
        response = json.loads(message)

        if 'error' in response:
            print(
                "Error during register_wallet : {0}".format(
                    response['error']))

        if 'wallet_id' in response:
            print("Wallet created : {}".format(response["wallet_id"]))
            return

    async def get_ca_server_info(self):
        command = {"command": "ca_server_info", "args": {}}
        message = json.dumps(command)
        await self.socket.send(message)
        message = await self.socket.recv()
        response = json.loads(message)
        return response
