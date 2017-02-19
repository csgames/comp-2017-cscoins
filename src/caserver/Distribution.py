
class Distribution:
    def __init__(self, submission_id, challenge_id, value, alias, wallet_nid, created_on=0, id=0):
        self.id = id
        self.submission_id = submission_id
        self.challenge_id = challenge_id
        self.value = value
        self.alias = alias
        self.wallet_nid = wallet_nid
        self.created_on = created_on