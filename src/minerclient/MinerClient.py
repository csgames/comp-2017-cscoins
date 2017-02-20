import json
import os
import ChallengeSolver
import time
from Crypto.Hash import SHA256
from coinslib import BaseClient
from coinslib import Challenge


class MinerClient(BaseClient):
    def __init__(self, key_dirs="", hostname="localhost"):
        BaseClient.__init__(self, hostname)
        self.keys_dir = key_dirs
        self.time_limit = 0
        self.solvers = []
        self.solvers.append(ChallengeSolver.SortedListSolver())
        self.solvers.append(ChallengeSolver.ReverseSortedListSolver())

    async def client_loop(self):
        register_wallet = False
        pub_path = "key.pub"
        priv_path = "key.priv"

        if len(self.keys_dir) > 0:
            pub_path = os.path.join(self.keys_dir, pub_path)
            priv_path = os.path.join(self.keys_dir, priv_path)

        if os.path.exists(pub_path) and os.path.exists(priv_path):
            self.load_keys(pub_path, priv_path)

        else:
            self.generate_wallet_keys()
            self.export_keys(pub_path, priv_path)
            register_wallet = True

        # generating wallet id
        self.generate_wallet_id()

        await self.connect()

        if register_wallet:
            # create the wallet
            keyString = ""
            for b in self.public_key.exportKey(format='PEM'):
                keyString += chr(b)

            hasher = SHA256.new()
            hasher.update(self.public_key.exportKey(format='DER'))
            signature = self.sign_message(hasher)

            command = {"command": "register_wallet", "args": {"name": 'miner_wallet', "key": keyString, "signature": signature}}
            message = json.dumps(command)
            await self.socket.send(message)
            message = await self.socket.recv()
            response = json.loads(message)

            if response['success']:
                print("Wallet created : {}".format(response["wallet_id"]))
                return

        await self.mine_loop()

    async def mine_loop(self):
        while True:
            print("Fetching current challenge")
            response = await self.get_current_challenge()
            current_challenge = Challenge()
            current_challenge.fill_from_challenge(response)
            self.time_limit = int(time.time()) + int(response['time_left'])
            print(response)
            solver = None

            for s in self.solvers:
                if s.challenge_name == current_challenge.challenge_name:
                    solver = s
                    break

            if solver:
                print("Searching for a hash matching : {0}".format(current_challenge.hash_prefix))
                result = solver.solve(current_challenge.parameters, current_challenge.hash_prefix, current_challenge.last_solution_hash)
                print(result)
                await self.submit(current_challenge.id, result[1], result[0])
            else:
                print("Solver for {0} not found".format(current_challenge.challenge_name))


