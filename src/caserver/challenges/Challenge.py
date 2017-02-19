class Challenge:

    # Solution Status
    (NotSet, Created, InProgress, Ended) = (0, 1, 2, 3)

    def __init__(self, challenge_name, nonce, solution_string, hash, parameters={}):
        self.challenge_name = challenge_name
        self.nonce = nonce
        self.solution_string = solution_string
        self.hash = hash
        self.parameters = parameters
        self.coin_value = 0
        self.id = 0
        self.duration = 0
        self.hash_prefix = ""
        self.created_on = 0
        self.started_on = 0
        self.status = self.NotSet

    def fill_prefix(self, length):
        self.hash_prefix = self.hash[0:length]

    def expiration(self):
        return self.started_on + (self.duration * 60)