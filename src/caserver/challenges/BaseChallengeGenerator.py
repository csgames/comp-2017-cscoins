import hashlib
import random


class BaseChallengeGenerator:
    def __init__(self, problem_name, config_file):
        self.problem_name = problem_name
        self.parameters = {}
        self.config_file = config_file
        self.nonce_min = 0
        self.nonce_max = 0

    def read_nonce_limit(self):
        self.nonce_min = self.config_file.get_int('challenge.nonce_min', 0)
        self.nonce_max = self.config_file.get_int('challenge.nonce_min', 99999999)

    def read_parameters(self):
        pass

    def generate(self, previous_solutions):
        """Generate a new problem and the solution"""
        pass

    def generate_solution(self, previous_solutions, nonce):
        pass

    def generate_seed_hash(self, previous_solutions, nonce):
        last_hash = self.last_solution_hash(previous_solutions)

        hasher = hashlib.sha256()
        hasher.update("{0}{1}".format(last_hash, nonce).encode('ascii'))
        hash_seed = hasher.hexdigest()
        return hash_seed

    def last_solution_hash(self, previous_solutions):
        # if none, the hash is 0
        if len(previous_solutions) > 0:
            return previous_solutions[-1].hash
        else:
            hash = "0" * 64
            return hash

    def generate_hash(self, previous_solutions, solution_string):
        sha256 = hashlib.sha256()

        for solution in previous_solutions:
            sha256.update("{0}".format(solution.solution_string).encode("ascii"))

        sha256.update("{0}".format(solution_string).encode("ascii"))

        return sha256.hexdigest()

    def generate(self, previous_solutions):
        # generate a nonce
        nonce = random.randint(self.nonce_min, self.nonce_max)
        print("Generating {0} problem nonce = {1}".format(self.problem_name, nonce))
        self.read_parameters()

        return self.generate_solution(previous_solutions, nonce)