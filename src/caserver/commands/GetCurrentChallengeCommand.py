from .BaseCommand import BaseCommand
import time
from caserver.challenges import Challenge

class GetCurrentChallengeCommand(BaseCommand):
    def __init__(self, central_authority_server):
        BaseCommand.__init__(self, central_authority_server, 'get_current_challenge')
        self.database = self.central_authority_server.database

    def execute(self, response, client_connection, args):

        current_challenge = self.database.get_current_challenge()
        last_solution = self.database.get_challenge_by_id(current_challenge.id - 1, Challenge.Ended)

        # subscribing to new challenge message push
        if client_connection is not None:
            client_connection.is_miner = True

        if current_challenge:
            timestamp = int(time.time())
            response['challenge_id'] = current_challenge.id
            response['challenge_name'] = current_challenge.challenge_name
            response['parameters'] = current_challenge.parameters
            current_challenge.fill_prefix(self.central_authority_server.prefix_length)
            response['hash_prefix'] = current_challenge.hash_prefix
            if last_solution is None:
                response['last_solution_hash'] = "0" * 64
            else:
                response['last_solution_hash'] = last_solution.hash
            time_left = current_challenge.expiration() - timestamp
            if time_left < 0:
                time_left = 0

            response['time_left'] = time_left
        else:
            return
