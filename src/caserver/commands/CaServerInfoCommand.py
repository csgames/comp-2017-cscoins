from .BaseCommand import BaseCommand


class CaServerInfoCommand(BaseCommand):
    def __init__(self, central_authority_server):
        BaseCommand.__init__(self, central_authority_server, 'ca_server_info')

    def execute(self, response, client_connection, args):
        response['success'] = True
        response['minutes_per_challenge'] = self.central_authority_server.minutes_per_challenge
        response['coins_per_challenge'] = self.central_authority_server.coins_per_challenge
        response['min_transaction_amount'] = self.central_authority_server.min_transaction_amount
        response['ca_public_key'] = self.central_authority_server.ca_public_key.exportKey(format='PEM')

    


