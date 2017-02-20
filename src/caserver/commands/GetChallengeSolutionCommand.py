from .BaseCommand import BaseCommand
from caserver.challenges.Challenge import Challenge


class GetChallengeSolutionCommand(BaseCommand):
    def __init__(self, central_authority_server):
        BaseCommand.__init__(self, central_authority_server, 'get_challenge_solution')
        self.database = self.central_authority_server.database

    def execute(self, response, client_connection, args):
        try:
            challenge_id = int(args['challenge_id'])

            if challenge_id > 0:
                challenge = self.database.get_challenge_by_id(challenge_id, Challenge.Ended)

                if challenge:
                    response['challenge_id'] = challenge.id
                    response['nonce'] = challenge.nonce
                    response['hash'] = challenge.hash
                    response['challenge_name'] = challenge.challenge_name
            else:
                response['challenge_id'] = 0
                response['nonce'] = 0
                response['hash'] = "0" * 64
                response['challenge_name'] = "initial_challenge"

        except KeyError as e:
            response["error"] = "Missing argument(s)"