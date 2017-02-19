
class BaseCommand:
    def __init__(self, central_authority_server, command_name):
        self.central_authority_server = central_authority_server
        self.command_name = command_name

    def execute(self, response, client_connection, args):
        pass