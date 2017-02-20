
class Challenge:
    def __init__(self, challenge_id=0, challenge_name=""):
        self.id = challenge_id
        self.challenge_name = challenge_name
        self.parameters = {}
        self.nonce = 0
        self.hash = ""
        self.hash_prefix = ""
        self.solution_string = ""
        self.last_solution_hash = ""

    def fill_from_solution(self, solution_dict):
        self.id = int(solution_dict['challenge_id'])
        self.hash = solution_dict['hash']
        self.challenge_name = solution_dict['challenge_name']
        self.nonce = int(solution_dict['nonce'])

    def fill_from_challenge(self, challenge_dict):
        self.id = int(challenge_dict['challenge_id'])
        self.challenge_name = challenge_dict['challenge_name']
        self.parameters = challenge_dict['parameters']
        self.hash_prefix = challenge_dict['hash_prefix']
        self.last_solution_hash = challenge_dict['last_solution_hash']
