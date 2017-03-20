import time


class ChallengeDisqualification:
    def __init__(self, wallet_nid, challenge_id, added_on=None, id=0):
        self.wallet_nid = wallet_nid
        self.challenge_id = challenge_id

        if added_on is None:
            added_on = int(time.time())

        self.added_on = added_on
        self.id = id


class ClientRequest:
    def __init__(self, remote_ip, command, requested_on=None, id=0):
        if requested_on is None:
            requested_on = int(time.time())

        self.id = id
        self.remote_ip = remote_ip
        self.command = command
        self.requested_on = requested_on


class SubmissionCooldown:
    def __init__(self, wallet_nid, length, end_on=None, id=0):
        if end_on is None:
            end_on = int(time.time()) + length

        self.id = id
        self.wallet_nid = wallet_nid
        self.length = length
        self.end_on = end_on


class ClientCooldown:
    def __init__(self, remote_ip, length, end_on=None, id=0):
        if end_on is None:
            end_on = int(time.time()) + length

        self.id = id
        self.remote_ip = remote_ip
        self.length = length
        self.end_on = end_on


class InvalidSubmission:
    def __init__(self, remote_ip, wallet_nid, verified_on=None, id=0):
        self.id = id
        self.wallet_nid = wallet_nid

        if verified_on is None:
            verified_on = int(time.time())

        self.remote_ip = remote_ip
        self.verified_on = verified_on
