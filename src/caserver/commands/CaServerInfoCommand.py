from .BaseCommand import BaseCommand


class CaServerInfoCommand(BaseCommand):
    def __init__(self, central_authority_server):
        BaseCommand.__init__(self, central_authority_server, 'ca_server_info')
        self.database = self.central_authority_server.database

    def execute(self, response, client_connection, args):
        response['type'] = 'ca_server_info'
        response['minutes_per_challenge'] = "{0:.5f}".format(
            self.central_authority_server.minutes_per_challenge)
        response['min_transaction_amount'] = "{0:.5f}".format(
            self.central_authority_server.min_transaction_amount)
        response['ca_public_key'] = self.central_authority_server.ca_public_key.exportKey(
            format='PEM').decode()
        response['coins_per_challenge'] = "{0:.5f}".format(
            self.central_authority_server.coins_per_challenge)

        current_challenge = self.database.get_current_challenge()
        if current_challenge is not None:
            response['coins_per_challenge'] = "{0:.5f}".format(
                current_challenge.coin_value)
            response['minutes_per_challenge'] = "{0:.5f}".format(
                current_challenge.duration)
