import json
import os
import ChallengeSolver
import time
from Crypto.Hash import SHA256
from coinslib import BaseClient
from coinslib import Challenge
import websockets
import asyncio

class MinerClient(BaseClient):
    def __init__(self, key_dirs="", hostname="localhost"):
        BaseClient.__init__(self, hostname)
        self.keys_dir = key_dirs
        self.time_limit = 0
        self.solvers = {}
        self.solvers["sorted_list"] = ChallengeSolver.SortedListSolver
        self.solvers["reverse_sorted_list"] = ChallengeSolver.ReverseSortedListSolver

        self.solving_thread = None

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
            await self.register_wallet()

        await self.mine_loop()

    async def get_challenge(self):
        response = await self.get_current_challenge()
        current_challenge = Challenge()
        current_challenge.fill_from_challenge(response)
        self.time_limit = int(time.time()) + int(response['time_left'])
        return current_challenge

    async def solve_challenge(self, challenge):
        solver = None
        try:
            solver = self.solvers[challenge.challenge_name]

        except KeyError:
            print("Solver not found for {0}...".format(challenge.challenge_name))

        self.solving_thread = solver(challenge)
        print("Starting solving thread {0}".format(self.solving_thread.challenge_name))
        self.solving_thread.start()

        while not self.solving_thread.solution_found and self.solving_thread.alive:
            await asyncio.sleep(0.2)

        return self.solving_thread.solution

    async def wait_for_new_challenge(self):
        msg = await self.socket.recv()
        response = json.loads(msg)
        current_challenge = Challenge()
        try:
            current_challenge = Challenge()
            current_challenge.fill_from_challenge(response)
            self.time_limit = int(time.time()) + int(response['time_left'])
            print("New challenge received")
        except:
            current_challenge = None

        return current_challenge

    async def mine_loop(self):
        print("Fetching current challenge")
        current_challenge = await self.get_challenge()
        while True:
            new_challenge = False
            while not new_challenge:
                mine_task = asyncio.ensure_future(self.solve_challenge(current_challenge))
                recv_task = asyncio.ensure_future(self.wait_for_new_challenge())
                done, pending = await asyncio.wait([recv_task, mine_task], return_when=asyncio.FIRST_COMPLETED)

                if mine_task in done:
                    solution = mine_task.result()
                    result = await self.submit(current_challenge.id, solution[1], solution[0])
                    if result is not None:
                        # we got a new challenge, right after the submission
                        recv_task.cancel()
                        current_challenge = result
                        new_challenge = True
                    else:
                        await asyncio.wait([recv_task], return_when=asyncio.FIRST_COMPLETED)
                        challenge = recv_task.result()
                        if challenge is not None:
                            new_challenge = True
                            current_challenge = challenge
                            continue
                else:
                    self.solving_thread.alive = False
                    mine_task.cancel()

                if recv_task in done:
                    self.solving_thread.alive = False
                    mine_task.cancel()
                    challenge = recv_task.result()
                    if challenge is not None:
                        new_challenge = True
                        current_challenge = challenge
                else:
                    recv_task.cancel()

                asyncio.sleep(0.01)