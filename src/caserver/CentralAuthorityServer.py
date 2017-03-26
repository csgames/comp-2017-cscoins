import asyncio
import websockets
import json
import Wallet
import os
import commands
import ConfigurationFile
import ServerStatistic
import ssl
import decimal
import ServerDatabase
import ChallengeThread
import RequestControl

from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto import Random


class ClientConnection:
    (Open, Closing, Closed) = (0, 1, 2)

    def __init__(self, websocket, status=Open):
        self.websocket = websocket
        self.status = status
        self.authenticated = False
        self.wallet = None
        self.is_miner = False
        self.messages_to_push = []

    def push_message(self, msg):
        self.messages_to_push.append(msg)

    def get_remote_ip(self):
        return self.websocket.remote_address[0]


class CentralAuthorityServer(object):

    def __init__(self):
        decimal.getcontext().prec = 5
        self.config_file = ConfigurationFile.ConfigurationFile()
        self.port = 8989
        self.listen_address = "localhost"
        self.server_socket = None
        self.wallets = []
        self.authority_wallet = None
        self.clients = []
        self.ca_name = "unnamed"
        self.transactions = []
        self.coins_per_challenge = 0
        self.minutes_per_challenge = 0
        self.ssl_on = True
        self.ssl_cert = ""
        self.available_challenges = []
        self.prefix_length = 4
        self.challenge_thread = None
        self.max_requests_per_minutes = 30
        self.initial_cooldown_length = 60
        self.invalid_submission_allowed = 5  # within 5 minutes
        self.supervisor_key = ''
        self.emit_coins = False

        self.min_transaction_amount = 0
        self.submissions_allowed_ips = []
        self.statistic = ServerStatistic.ServerStatistic()
        self.read_vars_from_config()
        self.database = ServerDatabase.ServerDatabase(
            self.config_file.get_string(
                "db_user", "cacoins"), self.config_file.get_string(
                "db_password", ""), self.config_file.get_string(
                "db_name", "cacoins"))

        # commands handler
        self.commands_handler = []
        self.fill_commands_handler()

        self.ca_private_key = None
        self.ca_public_key = None
        self.ca_wallet_id = None

        self.wallet_keys = {}

    def read_vars_from_config(self):
        self.config_file.read_file()
        self.port = self.config_file.get_int('port', 8989)
        self.listen_address = self.config_file.get_string(
            'listen_address', 'localhost')
        self.ssl_on = self.config_file.get_bool('ssl_on', True)
        self.ssl_cert = self.config_file.get_string(
            'ssl_cert', '../server.pem')

        self.ca_name = self.config_file.get_string(
            'ca_name', 'CS Games Coin Authority')

        self.coins_per_challenge = self.config_file.get_decimal(
            'coins_per_challenge', 10)
        self.minutes_per_challenge = self.config_file.get_decimal(
            'minutes_per_challenge', 15)

        self.min_transaction_amount = self.config_file.get_decimal(
            'min_transaction_amount', .00001)
        self.available_challenges = self.config_file.get_string_tuple(
            'available_challenges', ['sorted_list', 'reverse_sorted_list', 'shortest_path'])
        self.prefix_length = self.config_file.get_int('prefix_length', 4)
        self.max_requests_per_minutes = self.config_file.get_int(
            'max_requests_per_minutes', 30)
        self.initial_cooldown_length = self.config_file.get_int(
            'initial_cooldown_length', 60)
        self.invalid_submission_allowed = self.config_file.get_int(
            'invalid_submission_allowed', 5)
        self.supervisor_key = self.config_file.get_string('supervisor_key', '')
        self.emit_coins = self.config_file.get_bool('emit_coins', True)

        submissions_ips = self.config_file.get_string(
            'submissions_allowed_ips', '')
        submissions_allowed_ips = []
        if len(submissions_ips) > 0:
            ips = submissions_ips.split(',')
            for ip in ips:
                ip_str = ip.lstrip().rstrip()
                if len(ip_str) > 0:
                    submissions_allowed_ips.append(ip_str)

        self.submissions_allowed_ips = submissions_allowed_ips

    def fill_commands_handler(self):
        self.commands_handler.append(commands.GetCurrentChallengeCommand(self))
        self.commands_handler.append(
            commands.GetChallengeSolutionCommand(self))
        self.commands_handler.append(commands.RegisterWalletCommand(self))
        self.commands_handler.append(commands.SubmissionCommand(self))
        self.commands_handler.append(commands.GetTransactionsCommand(self))
        self.commands_handler.append(commands.CreateTransactionCommand(self))
        self.commands_handler.append(commands.CaServerInfoCommand(self))
        self.commands_handler.append(commands.CloseCommand(self))

    def is_ip_allowed_to_submit(self, remote_ip):
        if len(self.submissions_allowed_ips) == 0:
            return True

        return remote_ip in self.submissions_allowed_ips

    async def execute_client_command(self, client_connection, command, args):
        command_handler = None
        response = {}
        for ch in self.commands_handler:
            if ch.command_name == command:
                command_handler = ch

        if command_handler is None:
            print("Invalid command : {0}".format(command))
        else:
            command_handler.execute(response, client_connection, args)

        return json.dumps(response)

    async def handle_client(self, websocket):
        client_connection = ClientConnection(websocket)
        remote_addr = websocket.remote_address
        self.clients.append(client_connection)

        recv_task = None
        while not client_connection.status == ClientConnection.Closed:
            # messages pending to be push to the client
            if len(client_connection.messages_to_push) > 0:
                for m in client_connection.messages_to_push:
                    await websocket.send(m)

                client_connection.messages_to_push = []

            message = ""
            if recv_task is None:
                recv_task = asyncio.ensure_future(websocket.recv())
                continue
            elif recv_task.done():
                message = recv_task.result()
                recv_task = None
            else:
                await asyncio.sleep(0.2)
                continue

            # checking for cooldown
            if self.database.is_client_on_cooldown(remote_addr[0]):
                response = json.dumps(
                    {'error': '{0} is currently under a cooldown for request abuse.'.format(remote_addr[0])})
                await websocket.send(response)
                continue

            command_obj = json.JSONDecoder().decode(message)
            client_request = RequestControl.ClientRequest(
                remote_addr[0], message)
            self.database.add_client_request(client_request)

            try:
                command = command_obj["command"]
                args = command_obj["args"]

                if command == 'close':
                    websocket.close()
                    client_connection.status = ClientConnection.Closed
                    print(
                        "Connection closed ({0}:{1})".format(
                            remote_addr[0], remote_addr[1]))
                    break

                print(
                    "({0}:{1}) Executing command : {2}".format(
                        remote_addr[0],
                        remote_addr[1],
                        command))

                request_count = self.database.get_client_request_count(
                    remote_addr[0])

                if request_count <= self.max_requests_per_minutes:
                    try:
                        response = await self.execute_client_command(client_connection, command, args)
                    except Exception as e:
                        print(
                            "Error during execute_client_command: {0}".format(e))
                else:
                    cooldown_length = self.initial_cooldown_length
                    lastest_cooldown = self.database.get_client_latest_cooldown(
                        remote_addr[0])
                    if lastest_cooldown is not None:
                        cooldown_length = lastest_cooldown.length * 2
                    print(
                        "Client {0} has been put on a cooldown for {1} minutes. (Too much requests per minutes)".format(
                            remote_addr[0], int(
                                cooldown_length / 60)))
                    client_cooldown = RequestControl.ClientCooldown(
                        remote_addr[0], cooldown_length)
                    self.database.add_client_cooldown(client_cooldown)

                    response = json.dumps(
                        {
                            'error': 'Too much requests in one minute, you\'ve been put on cooldown for {0} minutes'.format(
                                cooldown_length /
                                60)})

                if client_connection.status == ClientConnection.Closing:
                    await websocket.close()
                    client_connection.status == ClientConnection.Closed
                    self.clients.remove(client_connection)

                await websocket.send(response)

            except Exception as e:
                print("Error occurred ({0}) closing connection".format(e))
                websocket.close()
                client_connection.status = ClientConnection.Closed
                self.clients.remove(client_connection)
                break

            await asyncio.sleep(0.5)

    async def handle_supervisor(self, websocket):
        while True:
            try:
                msg = await websocket.recv()
                message = json.loads(msg)

                supervisor_key = message['supervisor_key']
                wallet_id = message['wallet_id']
                if supervisor_key == self.supervisor_key:
                    current_challenge = self.database.get_current_challenge()
                    if current_challenge is None:
                        continue

                    wallet = self.database.get_wallet_by_id(wallet_id)

                    if wallet is not None:
                        disqualification = RequestControl.ChallengeDisqualification(
                            wallet.nid, current_challenge.id)
                        self.database.add_challenge_disqualification(
                            disqualification)
                        print(
                            "Wallet {0} is disqualified for challenge {1}".format(
                                wallet.id, current_challenge.id))

            except Exception as e:
                print("Error in handle_supervisor : {0}".format(e))
                break

            await asyncio.sleep(0.5)

    async def handle_connection(self, websocket, path):
        remote_addr = websocket.remote_address
        print(
            "Accepting a connection from {0}:{1}".format(
                remote_addr[0],
                remote_addr[1]))

        try:
            if path == '/client':
                await self.handle_client(websocket)
            elif path == '/supervisor':
                await self.handle_supervisor(websocket)
            else:
                websocket.close()
        except Exception as e:
            print(
                "Error occured with connection {0}:{1}, {2}".format(
                    remote_addr[0], remote_addr[1], e))

    def push_message_to_miners(self, message):
        for c in self.clients:
            if c.is_miner:
                c.push_message(message)

    def initialize(self):
        if not os.path.exists(
                'ca_key.priv') and not os.path.exists('ca_key.pub'):
            print("Generating CA Key pair")
            prng = Random.new().read

            key = RSA.generate(1024, prng)
            # saving key
            fp = open('ca_key.priv', 'wb')
            fp.write(key.exportKey(format='PEM'))
            fp.close()

            fp = open('ca_key.pub', 'wb')
            fp.write(key.publickey().exportKey(format='PEM'))
            fp.close()

            self.ca_private_key = key
            self.ca_public_key = key.publickey()
        else:
            fp = open('ca_key.priv', 'rb')
            f_priv_key = fp.read(4096)
            fp.close()

            fp = open('ca_key.pub', 'rb')
            f_pub_key = fp.read(4096)
            fp.close()

            self.ca_private_key = RSA.importKey(f_priv_key)
            self.ca_public_key = RSA.importKey(f_pub_key)

        # computing wallet id
        # hashing the public key
        hasher = SHA256.new()
        hasher.update(self.ca_public_key.exportKey(format='DER'))
        self.ca_wallet_id = hasher.hexdigest()

        self.database.init_schema()

        # loading from db
        print("Loading wallets from Database")
        self.wallets = self.database.get_wallets(0, 1000)

        for w in self.wallets:
            if w.id == self.ca_wallet_id:
                self.authority_wallet = w

        if self.authority_wallet is None:
            print("Creating CA Wallet")
            keyString = ""
            for b in self.ca_public_key.exportKey(format='PEM'):
                keyString += chr(b)

            w = Wallet.Wallet(self.ca_name, keyString, self.ca_wallet_id)
            self.database.create_wallet(w)
            self.wallets.append(w)
            print("CA Wallet Id -> {0}".format(self.ca_wallet_id))
            # Wallet.save_wallets(self.wallets)
            self.authority_wallet = w

        print("Loading transactions...")

        i = 0
        txns = self.database.get_transactions(i, 100)

        while len(txns) == 100:
            for t in txns:
                self.transactions.append(t)

            i += 100
            txns = self.database.get_transactions(i, 100)

        for t in txns:
            self.transactions.append(t)

        # computing wallet balance
        self.calculate_wallets_balance()

        # saving wallet balance
        self.save_wallets()

    def save_wallets(self):
        for w in self.wallets:
            self.database.add_wallet_balance(w)

    def calculate_wallets_balance(self):
        for t in self.transactions:
            try:
                source_wallet = self.resolve_wallet(t.source)
                recipient_wallet = self.resolve_wallet(t.recipient)

                if source_wallet is None or recipient_wallet is None:
                    print("Invalid transaction {0}".format(t.id))

                if source_wallet == recipient_wallet:
                    print("Invalid transaction {0}".format(t.id))

                source_pub_key = RSA.importKey(source_wallet.key)

                # verify signature
                if not t.verify_signature(source_pub_key):
                    print("Invalid signature for Txn #{0}".format(t.id))
                    continue

                if t.amount >= self.min_transaction_amount:
                    if source_wallet.balance >= t.amount or source_wallet.id == self.authority_wallet.id:
                        source_wallet.balance -= t.amount
                        recipient_wallet.balance += t.amount
                    else:
                        print("Invalid transaction {0}".format(t.id))
                else:
                    print("Invalid transaction {0}".format(t.id))

            except Exception as e:
                print("calculate_wallets_balance exception : {0}".format(e))

    def resolve_wallet(self, address):
        for w in self.wallets:
            if w.id == address:
                return w
        return None

    def serve(self):
        self.initialize()

        self.challenge_thread = ChallengeThread.ChallengeThread(self)
        self.challenge_thread.start()

        if self.ssl_on:
            ssl_context = ssl.SSLContext(protocol=ssl.PROTOCOL_SSLv23)
            ssl_context.load_cert_chain(self.ssl_cert)
            self.server_socket = websockets.serve(
                self.handle_connection, self.listen_address, self.port, ssl=ssl_context)
        else:
            self.server_socket = websockets.serve(
                self.handle_connection, self.listen_address, self.port)

        try:
            asyncio.get_event_loop().run_until_complete(self.server_socket)
            asyncio.get_event_loop().run_forever()
        except KeyboardInterrupt:
            print("Closing the server")
            asyncio.get_event_loop().close()
