import threading
from challenges import *
import random
import time
import decimal
import Transaction
import commands
import json
import Distribution
from Crypto.PublicKey import RSA


class ChallengeThread(threading.Thread):
    def __init__(self, central_authority_server):
        threading.Thread.__init__(self)
        self.central_authority_server = central_authority_server
        self.database = self.central_authority_server.database
        self.current_challenge = None
        self.previous_challenge = []
        self.generators = []
        self.alive = True
        self.last_solution_hash = "0" * 64
        self.current_challenge_command = commands.GetCurrentChallengeCommand(central_authority_server)
        self.__init_generators()
        self.__init_challenges()

    def __init_generators(self):
        self.generators.append(ReverseSortedListChallenge(self.central_authority_server.config_file))
        self.generators.append(SortedListChallenge(self.central_authority_server.config_file))

    def __init_challenges(self):
        # loading challenges
        challenges = []
        challenge_index = 0
        last_challenges = self.database.get_challenges(challenge_index)

        while len(last_challenges) == 100:
            for c in last_challenges:
                if c.status == Challenge.Ended:
                    challenges.append(c)
                elif c.status == Challenge.InProgress:
                    print("Challenge In Progress found #{0}".format(c.id))
                    self.current_challenge = c

            challenge_index += len(last_challenges)
            last_challenges = self.database.get_challenges(challenge_index)

        for c in last_challenges:
            if c.status == Challenge.InProgress:
                print("Challenge In Progress found #{0}".format(c.id))
                self.current_challenge = c
            elif c.status == Challenge.Ended:
                challenges.append(c)

        self.previous_challenge = challenges

        if self.current_challenge is None:
            print("No current challenge, generating a new challenge")
            challenge_history = []
            for c in self.previous_challenge:
                challenge_history.append(c)

            if len(challenge_history) > 0:
                self.last_solution_hash = challenge_history[-1].hash

            self.current_challenge = self.generate_new_challenge()
            challenge_history.append(self.current_challenge)

            self.current_challenge.status = Challenge.InProgress
            self.current_challenge.started_on = int(time.time())
            self.database.update_challenge(self.current_challenge)
            print("New challenge generated for {0} minutes".format(self.current_challenge.duration))

    def run(self):
        while self.alive:
            timestamp = int(time.time())

            if timestamp > self.current_challenge.expiration():
                self.end_challenge()
                self.next_challenge()
            else:
                submissions = self.database.get_submissions(self.current_challenge.id)
                authority_wallet = self.database.get_wallet_by_nid(self.central_authority_server.authority_wallet.nid)
                ca_private_key = self.central_authority_server.ca_private_key
                for submission in submissions:
                    if submission.submitted_on < self.current_challenge.expiration():

                        # winning submission !
                        # verify the solution
                        generator = None
                        for g in self.generators:
                            if g.problem_name == self.current_challenge.challenge_name:
                                generator = g

                        solution = generator.generate_solution(self.last_solution_hash, submission.nonce)

                        if solution.hash.startswith(self.current_challenge.hash_prefix):
                            # we got a solution
                            print("Solution valid Original Nonce:{0}  Solution Nonce:{1}".format(self.current_challenge.nonce, solution.nonce))

                            self.current_challenge.hash = solution.hash
                            self.current_challenge.solution_string = solution.solution_string
                            self.current_challenge.nonce = solution.nonce

                            self.database.update_solution(self.current_challenge)

                            self.end_challenge()

                            # giving some coins !
                            coin_value = decimal.Decimal(self.current_challenge.coin_value)

                            recipient_wallet = self.database.get_wallet_by_nid(submission.wallet.nid)

                            txn = Transaction.Transaction(0, authority_wallet.id, recipient_wallet.id, coin_value)
                            txn.sign_with(ca_private_key)

                            print("{0} + {1:.5f} Coins".format(recipient_wallet.id, coin_value))
                            self.database.create_transaction(txn)

                            authority_wallet.balance -= coin_value
                            recipient_wallet.balance += coin_value

                            self.database.update_wallet_balance(recipient_wallet)

                            self.next_challenge()

                            break
                        else:
                            print("Invalid submission from {0}, deleting from Database".format(submission.wallet.id))
                            self.database.delete_submission(submission)
                    else:
                        print("Submission #{0} has a timestamp before the current challenge!".format(submission.id))

                self.database.update_wallet_balance(authority_wallet)
            time.sleep(0.2)

    def end_challenge(self):
        last_challenge = self.current_challenge
        last_challenge.status = Challenge.Ended
        self.last_solution_hash = last_challenge.hash
        self.database.update_challenge(last_challenge)
        self.previous_challenge.append(last_challenge)

    def next_challenge(self):
        created_challenges = self.database.get_challenges_by_status(0, 1, Challenge.Created)
        new_challenge = None
        if len(created_challenges) > 0:
            new_challenge = created_challenges[0]
        else:
            new_challenge = self.generate_new_challenge()

        new_challenge.status = Challenge.InProgress
        new_challenge.started_on = int(time.time())
        self.database.update_challenge(new_challenge)
        self.current_challenge = new_challenge

        # pushing new challenge message
        challenge_message = {}
        self.current_challenge_command.execute(challenge_message, None, None)
        self.central_authority_server.push_message_to_miners(json.dumps(challenge_message))

    def generate_new_challenge(self):
        # reload server config file
        self.central_authority_server.read_vars_from_config()

        challenge_name = random.choice(self.central_authority_server.available_challenges)
        generator = None
        for g in self.generators:
            if g.problem_name == challenge_name:
                generator = g
                break

        new_challenge = generator.generate(self.last_solution_hash)
        # reload server config file
        self.central_authority_server.read_vars_from_config()
        new_challenge.duration = self.central_authority_server.minutes_per_challenge
        new_challenge.coin_value = self.central_authority_server.coins_per_challenge
        new_challenge.fill_prefix(self.central_authority_server.prefix_length)
        self.database.add_challenge(new_challenge)
        return new_challenge
