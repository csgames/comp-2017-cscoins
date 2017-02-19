from .BaseCommand import BaseCommand
from caserver.CentralAuthorityServer import ClientConnection

class CloseCommand(BaseCommand):
    def __init__(self, central_authority_server):
        BaseCommand.__init__(self, central_authority_server, 'close')

    def execute(self, response, client_connection, args):
        try:
            client_connection.status = ClientConnection.Closing

        except Exception as e:
            print("{0} exception : {1}".format(self.__class__, e))