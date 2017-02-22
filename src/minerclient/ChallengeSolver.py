from coinslib import MT64, seed_from_hash
import hashlib
import random
import threading


class ChallengeSolver(threading.Thread):
    def __init__(self, challenge_name, challenge):
        threading.Thread.__init__(self)
        self.challenge_name = challenge_name
        self.mt = None
        self.alive = True
        self.solution_found = False
        self.solution = ()
        self.challenge = challenge

    def feed_prng(self, previous_hash, nonce):
        hasher = hashlib.sha256()
        hasher.update("{0}{1}".format(previous_hash, nonce).encode("ascii"))
        seed_hash = hasher.hexdigest()

        seed = seed_from_hash(seed_hash)
        self.mt = MT64(seed)

    def solve(self, parameters, hash_prefix, previous_hash):
        pass

    def run(self):
        self.solution = self.solve(self.challenge.parameters, self.challenge.hash_prefix, self.challenge.last_solution_hash)
        self.solution_found = True


class SortedListSolver(ChallengeSolver):
    def __init__(self, challenge):
        ChallengeSolver.__init__(self, 'sorted_list', challenge)

    def solve(self, parameters, hash_prefix, previous_hash):
        nb_elements = parameters['nb_elements']

        nonce = random.randint(0, 99999999)

        while self.alive:
            self.feed_prng(previous_hash, nonce)

            elements = []

            for i in range(nb_elements):
                elements.append(self.mt.extract_number())

            elements.sort()

            solution_string = ""
            for i in elements:
                solution_string += "{0}".format(i)

            sha256 = hashlib.sha256()
            sha256.update(solution_string.encode('ascii'))
            solution_hash = sha256.hexdigest()

            if solution_hash.startswith(hash_prefix):
                print("Solution found ! nonce:{0} hash:{1}".format(nonce, solution_hash))
                return solution_hash, nonce

            nonce = random.randint(0, 99999999)

class ReverseSortedListSolver(ChallengeSolver):
    def __init__(self, challenge):
        ChallengeSolver.__init__(self, 'reverse_sorted_list', challenge)

    def solve(self, parameters, hash_prefix, previous_hash):
        nb_elements = parameters['nb_elements']

        nonce = random.randint(0, 99999999)

        while self.alive:
            self.feed_prng(previous_hash, nonce)

            elements = []

            for i in range(nb_elements):
                elements.append(self.mt.extract_number())

            elements.sort(reverse=True)

            solution_string = ""
            for i in elements:
                solution_string += "{0}".format(i)

            sha256 = hashlib.sha256()
            sha256.update(solution_string.encode('ascii'))
            solution_hash = sha256.hexdigest()

            if solution_hash.startswith(hash_prefix):
                print("Solution found ! nonce:{0} hash:{1}".format(nonce, solution_hash))
                return solution_hash, nonce

            nonce = random.randint(0, 99999999)

