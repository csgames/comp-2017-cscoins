from .BaseChallengeGenerator import BaseChallengeGenerator
from .Challenge import Challenge
import random
import coinslib


class SortedListChallenge(BaseChallengeGenerator):
    def __init__(self, config_file):
        BaseChallengeGenerator.__init__(self, 'sorted_list', config_file)
        self.read_parameters()

    def read_parameters(self):
        self.config_file.read_file()
        self.parameters["nb_elements"] = self.config_file.get_int('sorted_list.nb_elements', 100)
        self.read_nonce_limit()

    def generate_solution(self, previous_hash, nonce):
        seed_hash = self.generate_seed_hash(previous_hash, nonce)
        prng = coinslib.MT64(coinslib.seed_from_hash(seed_hash))

        element_list = []

        # generate n elements
        for i in range(self.parameters["nb_elements"]):
            element_list.append(prng.extract_number())

        element_list.sort()

        solution_string = ""

        for i in element_list:
            solution_string += "{0}".format(i)

        hash = self.generate_hash(solution_string)

        return Challenge(self.problem_name, nonce, solution_string, hash, self.parameters)

