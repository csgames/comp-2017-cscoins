from .BaseCommand import BaseCommand

class GetTransactionsCommand(BaseCommand):
    def __init__(self, central_authority_server):
        BaseCommand.__init__(self, central_authority_server, "get_transactions")
        self.database = self.central_authority_server.database
        self.max_transactions = 100
        
    def execute(self, response, client_connection, args):
        try:
            start_transaction = int(args['start'])
            count = int(args['count'])

            if count > self.max_transactions:
                count = self.max_transactions

            transactions = self.database.get_transactions(start_transaction, count)
            
            response['transactions'] = []

            for t in transactions:
                response['transactions'].append({'id': t.id, 'source': t.source, 'recipient': t.recipient, 'amount': str(t.amount)})

            response['success'] = True
            response['count'] = len(transactions)

        except KeyError as e:
            response["error"] = "Missing argument(s)"
        except Exception as e:
            print("{0} exception : {1}".format(self.__class__, e))
