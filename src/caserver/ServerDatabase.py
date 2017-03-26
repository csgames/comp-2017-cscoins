import MySQLdb
import Transaction
import time
import Wallet
import RequestControl
import decimal
import json
from challenges import Challenge, Submission


class ServerDatabase:
    def __init__(self, username, password, db="cacoins",
                 hostname="localhost", port=3306):
        self.username = username
        self.password = password
        self.hostname = hostname
        self.port = port
        self.db = db

    def init_schema(self):
        conn = self.connect()
        cur = conn.cursor()

        cur.execute("""CREATE TABLE IF NOT EXISTS `wallets` (
                      `wallet_nid` int(11) NOT NULL AUTO_INCREMENT,
                      `wallet_id` varchar(64) NOT NULL,
                      `wallet_name` varchar(255) NOT NULL,
                      `wallet_key` TEXT NOT NULL,
                      `created_on` int(11) DEFAULT NULL,
                      PRIMARY KEY (`wallet_nid`)
                    ) ENGINE=InnoDB DEFAULT CHARSET=latin1;""")

        cur.execute("""CREATE TABLE IF NOT EXISTS `transactions` (
                      `transaction_id` int(11) NOT NULL AUTO_INCREMENT,
                      `source` varchar(64) NOT NULL,
                      `recipient` varchar(64) NOT NULL,
                      `amount` decimal(20,5) NOT NULL,
                      `signature` TEXT NOT NULL,
                      `created_on` int(11) DEFAULT NULL,
                      PRIMARY KEY (`transaction_id`)
                    ) ENGINE=InnoDB DEFAULT CHARSET=latin1;""")

        cur.execute("""CREATE TABLE IF NOT EXISTS `wallet_balances` (
                        `wallet_balance_id` INT NOT NULL AUTO_INCREMENT,
                        `wallet_nid` INT NOT NULL,
                        `wallet_balance` DECIMAL(20,5) NOT NULL,
                        PRIMARY KEY (`wallet_balance_id`)
                        ) ENGINE=InnoDB DEFAULT CHARSET=latin1;""")

        cur.execute("""CREATE TABLE IF NOT EXISTS `challenges` (
                        `challenge_id` INT NOT NULL AUTO_INCREMENT,
                        `challenge_name` VARCHAR(255) NOT NULL,
                        `solution_string` LONGTEXT NOT NULL,
                        `nonce` BIGINT UNSIGNED NOT NULL,
                        `coin_value` INT NOT NULL,
                        `hash` varchar(64) NOT NULL,
                        `parameters` TEXT NOT NULL,
                        `duration` INT NOT NULL,
                        `status` INT NOT NULL,
                        `created_on` INT NOT NULL,
                        `started_on` INT NOT NULL,
                        PRIMARY KEY (`challenge_id`)
                        ) ENGINE=InnoDB DEFAULT CHARSET=latin1;""")

        cur.execute("""CREATE TABLE IF NOT EXISTS `submissions` (
                        `submission_id` INT NOT NULL AUTO_INCREMENT,
                        `challenge_id` INT NOT NULL,
                        `nonce` BIGINT UNSIGNED NOT NULL,
                        `hash` varchar(64),
                        `wallet_nid` INT NOT NULL,
                        `submitted_on` INT NULL,
                        `remote_ip` VARCHAR(96) NOT NULL,
                        PRIMARY KEY (`submission_id`)
                    ) ENGINE=InnoDB DEFAULT CHARSET=latin1;""")

        cur.execute("""CREATE TABLE IF NOT EXISTS `clients_request` (
                        `client_request_id` INT NOT NULL AUTO_INCREMENT,
                        `remote_ip`  VARCHAR(96) NOT NULL,
                        `command` TEXT,
                        `requested_on` INT NOT NULL,
                        PRIMARY KEY (`client_request_id`)
                    ) ENGINE=InnoDB DEFAULT CHARSET=latin1;""")

        cur.execute("""CREATE TABLE IF NOT EXISTS `clients_cooldown` (
                    `client_cooldown_id` INT NOT NULL AUTO_INCREMENT,
                    `remote_ip` VARCHAR(96) NOT NULL,
                    `cooldown_length` INT NOT NULL,
                    `end_on` INT NOT NULL,
                    PRIMARY KEY (`client_cooldown_id`)
                    ) ENGINE=InnoDB DEFAULT CHARSET=latin1;""")

        cur.execute("""CREATE TABLE IF NOT EXISTS `invalid_submissions` (
                    `invalid_submission_id` INT NOT NULL AUTO_INCREMENT,
                    `remote_ip` VARCHAR(96) NOT NULL,
                    `wallet_nid` INT NOT NULL,
                    `verified_on` INT NOT NULL,
                    PRIMARY KEY (`invalid_submission_id`)
                    ) ENGINE=InnoDB DEFAULT CHARSET=latin1;""")

        cur.execute("""CREATE TABLE IF NOT EXISTS `submissions_cooldown` (
                    `submission_cooldown_id` INT NOT NULL AUTO_INCREMENT,
                    `wallet_nid` INT NOT NULL,
                    `cooldown_length` INT NOT NULL,
                    `end_on` INT NOT NULL,
                    PRIMARY KEY (`submission_cooldown_id`)
                    ) ENGINE=InnoDB DEFAULT CHARSET=latin1;""")

        cur.execute("""CREATE TABLE IF NOT EXISTS `challenge_disqualifications` (
                    `challenge_disqualification_id` INT NOT NULL AUTO_INCREMENT,
                    `wallet_nid` INT NOT NULL,
                    `challenge_id` INT NOT NULL,
                    `added_on` INT NOT NULL,
                    PRIMARY KEY (`challenge_disqualification_id`)
                    ) ENGINE=InnoDB DEFAULT CHARSET=latin1;""")

        cur.execute("""DELETE FROM wallet_balances;""")
        cur.execute("""DELETE FROM clients_request;""")

        conn.commit()

        cur.close()
        conn.close()

    def connect(self):
        conn = None
        try:
            conn = MySQLdb.Connect(
                host=self.hostname,
                port=self.port,
                user=self.username,
                password=self.password,
                db=self.db)
        except Exception as e:
            print("MySQL Connection error : {0}".format(e))

        return conn

    def get_invalid_submission_count(self, wallet_nid):
        time_start = int(time.time()) - (5 * 60)
        invalid_submission_count = 0
        conn = self.connect()
        cur = conn.cursor()

        query = """SELECT COUNT(invalid_submission_id) FROM invalid_submissions WHERE wallet_nid = %s AND verified_on >= %s"""
        cur.execute(query, (wallet_nid, time_start, ))

        row = cur.fetchone()
        if row:
            invalid_submission_count = row[0]

        cur.close()
        conn.close()
        return invalid_submission_count

    def add_challenge_disqualification(self, challenge_disqualification):
        conn = self.connect()
        cur = conn.cursor()

        query = """INSERT INTO challenge_disqualifications (challenge_id, wallet_nid, added_on) VALUES (%s, %s, %s)"""

        cur.execute(
            query,
            (challenge_disqualification.challenge_id,
             challenge_disqualification.wallet_nid,
             challenge_disqualification.added_on,
             ))

        conn.commit()
        cur.close()
        conn.close()

    def is_wallet_disqualified(self, challenge_id, wallet_nid):
        disqualified = False
        conn = self.connect()
        cur = conn.cursor()

        query = """SELECT wallet_nid FROM challenge_disqualifications WHERE challenge_id = %s AND wallet_nid = %s"""

        cur.execute(query, (challenge_id, wallet_nid, ))

        row = cur.fetchone()
        if row:
            disqualified = True

        cur.close()
        conn.close()
        return disqualified

    def add_invalid_submission(self, invalid_submission):
        conn = self.connect()
        cur = conn.cursor()

        query = """INSERT INTO invalid_submissions (remote_ip, wallet_nid, verified_on) VALUES (%s, %s, %s)"""
        cur.execute(
            query,
            (invalid_submission.remote_ip,
             invalid_submission.wallet_nid,
             invalid_submission.verified_on,
             ))

        conn.commit()
        cur.close()
        conn.close()

    def add_submission_cooldown(self, submission_cooldown):
        conn = self.connect()
        cur = conn.cursor()

        query = """INSERT INTO submissions_cooldown (wallet_nid, cooldown_length, end_on) VALUES (%s, %s, %s)"""

        cur.execute(
            query,
            (submission_cooldown.wallet_nid,
             submission_cooldown.length,
             submission_cooldown.end_on,
             ))

        conn.commit()
        cur.close()
        conn.close()

    def get_submission_latest_cooldown(self, wallet_nid):
        submission_cooldown = None
        conn = self.connect()
        cur = conn.cursor()

        query = """SELECT submission_cooldown_id, wallet_nid, cooldown_length, end_on FROM submissions_cooldown WHERE wallet_nid = %s ORDER BY submission_cooldown_id DESC"""

        cur.execute(query, (wallet_nid,))

        row = cur.fetchone()
        if row:
            submission_cooldown = RequestControl.SubmissionCooldown(
                row[1], row[2], row[3], row[0])

        cur.close()
        conn.close()

        return submission_cooldown

    def get_client_latest_cooldown(self, remote_ip):
        client_cooldown = None
        conn = self.connect()
        cur = conn.cursor()

        query = """SELECT client_cooldown_id, remote_ip, cooldown_length, end_on FROM clients_cooldown WHERE remote_ip = %s ORDER BY client_cooldown_id DESC"""

        cur.execute(query, (remote_ip, ))

        row = cur.fetchone()
        if row:
            client_cooldown = RequestControl.ClientCooldown(
                row[1], row[2], row[3], row[0])

        cur.close()
        conn.close()

        return client_cooldown

    def is_client_on_submission_cooldown(self, wallet_nid):
        timestamp = int(time.time())
        is_on_cooldown = False
        conn = self.connect()
        cur = conn.cursor()

        query = """SELECT submission_cooldown_id FROM submissions_cooldown WHERE wallet_nid = %s AND end_on > %s"""
        cur.execute(query, (wallet_nid, timestamp, ))

        row = cur.fetchone()

        if row:
            is_on_cooldown = True

        cur.close()
        conn.close()

        return is_on_cooldown

    def is_client_on_cooldown(self, remote_ip):
        timestamp = int(time.time())
        is_on_cooldown = False
        conn = self.connect()
        cur = conn.cursor()

        query = """SELECT client_cooldown_id FROM clients_cooldown WHERE remote_ip = %s AND end_on > %s"""
        cur.execute(query, (remote_ip, timestamp, ))

        row = cur.fetchone()

        if row:
            is_on_cooldown = True

        cur.close()
        conn.close()

        return is_on_cooldown

    def add_client_cooldown(self, client_cooldown):
        conn = self.connect()
        cur = conn.cursor()

        query = """INSERT INTO `clients_cooldown` (remote_ip, cooldown_length, end_on) VALUES (%s, %s, %s)"""
        cur.execute(
            query,
            (client_cooldown.remote_ip,
             client_cooldown.length,
             client_cooldown.end_on,
             ))

        conn.commit()
        cur.close()
        conn.close()

    def get_client_request_count(self, remote_ip):
        request_count = 0
        conn = self.connect()
        cur = conn.cursor()

        timestamp_start = int(time.time()) - 60

        query = """SELECT COUNT(client_request_id) FROM clients_request WHERE remote_ip = %s AND requested_on >= %s"""

        cur.execute(query, (remote_ip, timestamp_start, ))

        row = cur.fetchone()

        if row:
            request_count = row[0]

        cur.close()
        conn.close()

        return request_count

    def add_client_request(self, client_request):
        conn = self.connect()
        cur = conn.cursor()

        query = """INSERT INTO clients_request (remote_ip, command, requested_on) VALUES (%s, %s, %s)"""

        cur.execute(
            query,
            (client_request.remote_ip,
             client_request.command,
             client_request.requested_on,
             ))

        conn.commit()
        cur.close()
        conn.close()

    def update_challenge(self, challenge):
        if challenge.id > 0:
            conn = self.connect()
            cur = conn.cursor()

            query = """UPDATE challenges SET status = %s, started_on = %s WHERE challenge_id = %s"""

            cur.execute(
                query,
                (challenge.status,
                 challenge.started_on,
                 challenge.id,
                 ))

            conn.commit()

            cur.close()
            conn.close()

    def update_solution(self, challenge):
        if challenge.id > 0:
            conn = self.connect()
            cur = conn.cursor()

            query = """UPDATE challenges SET nonce = %s, hash = %s, solution_string = %s WHERE challenge_id = %s"""

            cur.execute(
                query,
                (challenge.nonce,
                 challenge.hash,
                 challenge.solution_string,
                 challenge.id,
                 ))

            conn.commit()

            cur.close()
            conn.close()

    def get_current_challenge(self):
        challenge = None
        conn = self.connect()
        cur = conn.cursor()

        query = """SELECT
            challenge_id,
            challenge_name,
            solution_string,
            nonce,
            coin_value,
            hash,
            parameters,
            status,
            duration,
            created_on,
            started_on
            FROM challenges
            WHERE status = %s
            ORDER BY challenge_id DESC LIMIT 1"""

        rs = cur.execute(query, (Challenge.InProgress, ))

        row = cur.fetchone()

        if row:
            challenge = self.__fill_challenge_object(row)

        cur.close()
        conn.close()

        return challenge

    def __fill_challenge_object(self, row):
        params = json.loads(row[6])
        challenge = Challenge(row[1], int(row[3]), row[2], row[5], params)
        challenge.id = int(row[0])
        challenge.coin_value = int(row[4])
        challenge.status = int(row[7])
        challenge.duration = int(row[8])
        challenge.created_on = int(row[9])
        challenge.started_on = int(row[10])

        return challenge

    def get_challenges_by_status(
            self, start, count=100, status=Challenge.Created):
        challenges = []
        conn = self.connect()
        cur = conn.cursor()

        query = """SELECT
            challenge_id,
            challenge_name,
            solution_string,
            nonce,
            coin_value,
            hash,
            parameters,
            status,
            duration,
            created_on,
            started_on
            FROM challenges
            WHERE status = %s
            ORDER BY challenge_id
            LIMIT %s, %s"""

        rs = cur.execute(query, (status, start, count, ))
        rows = cur.fetchall()

        for row in rows:
            challenges.append(self.__fill_challenge_object(row))

        cur.close()
        conn.close()

        return challenges

    def get_challenge_by_id(self, challenge_id, status):
        challenge = None
        conn = self.connect()
        cur = conn.cursor()

        query = """SELECT
            challenge_id,
            challenge_name,
            solution_string,
            nonce,
            coin_value,
            hash,
            parameters,
            status,
            duration,
            created_on,
            started_on
            FROM challenges
            WHERE challenge_id = %s AND status = %s
            LIMIT 1"""

        rs = cur.execute(query, (challenge_id, status,))
        row = cur.fetchone()

        if row:
            challenge = self.__fill_challenge_object(row)

        cur.close()
        conn.close()

        return challenge

    def get_challenges(self, start, count=100):
        challenges = []
        conn = self.connect()
        cur = conn.cursor()

        query = """SELECT
            challenge_id,
            challenge_name,
            solution_string,
            nonce,
            coin_value,
            hash,
            parameters,
            status,
            duration,
            created_on,
            started_on
            FROM challenges
            LIMIT %s, %s"""

        rs = cur.execute(query, (start, count,))
        rows = cur.fetchall()

        for row in rows:
            challenges.append(self.__fill_challenge_object(row))

        cur.close()
        conn.close()

        return challenges

    def add_challenge(self, challenge):
        conn = self.connect()
        cur = conn.cursor()
        timestamp = int(time.time())
        parameters = json.dumps(challenge.parameters)
        challenge.created_on = timestamp
        challenge.status = Challenge.Created
        query = """INSERT INTO challenges (
            challenge_name,
            solution_string,
            nonce,
            coin_value,
            hash,
            parameters,
            status,
            duration,
            created_on,
            started_on)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 0)"""

        cur.execute(query, (challenge.challenge_name,
                            challenge.solution_string,
                            challenge.nonce,
                            challenge.coin_value,
                            challenge.hash,
                            parameters,
                            challenge.status,
                            challenge.duration,
                            timestamp, ))

        conn.commit()

        # fetching the challenge id
        query = """SELECT challenge_id FROM challenges WHERE hash = %s AND created_on = %s"""
        rs = cur.execute(query, (challenge.hash, challenge.created_on,))

        row = cur.fetchone()

        if row:
            challenge.id = int(row[0])

        cur.close()
        conn.close()

    def add_or_update_submission(self, submission):
        conn = self.connect()
        cur = conn.cursor()
        timestamp = int(time.time())

        query = """SELECT submission_id FROM submissions WHERE challenge_id = %s AND wallet_nid = %s"""
        rs = cur.execute(
            query, (submission.challenge_id, submission.wallet.nid,))

        row = cur.fetchone()
        if row:
            submission.id = row[0]
            query = """UPDATE submissions SET nonce = %s, submitted_on = %s, remote_ip = %s WHERE submission_id = %s"""
            rs = cur.execute(
                query,
                (submission.nonce,
                 timestamp,
                 submission.remote_ip,
                 submission.id,
                 ))
        else:
            query = """INSERT INTO submissions (challenge_id, nonce, wallet_nid, submitted_on, remote_ip) VALUES (%s, %s, %s, %s, %s)"""
            rs = cur.execute(
                query,
                (submission.challenge_id,
                 submission.nonce,
                 submission.wallet.nid,
                 timestamp,
                 submission.remote_ip,
                 ))

            query = """SELECT submission_id FROM submissions WHERE challenge_id = %s AND wallet_nid = %s AND submitted_on = %s"""
            rs = cur.execute(
                query,
                (submission.challenge_id,
                 submission.wallet.nid,
                 timestamp))
            row = cur.fetchone()
            if row:
                submission.id = int(row[0])

        conn.commit()

        cur.close()
        conn.close()

    def delete_submission(self, submission):
        if submission.id <= 0:
            return

        conn = self.connect()
        cur = conn.cursor()

        query = """DELETE FROM submissions WHERE submission_id = %s"""

        cur.execute(query, (submission.id, ))

        conn.commit()

        cur.close()
        conn.close()

    def get_submissions(self, challenge_id):
        submissions = []
        conn = self.connect()
        cur = conn.cursor()

        query = """SELECT
                        s.submission_id,
                        s.challenge_id,
                        s.nonce,
                        s.hash,
                        s.submitted_on,
                        w.wallet_nid,
                        w.wallet_id,
                        w.wallet_key,
                        w.wallet_name,
                        wb.wallet_balance,
                        s.remote_ip
                    FROM submissions s
                    JOIN wallets w ON s.wallet_nid = w.wallet_nid
                    JOIN wallet_balances wb ON wb.wallet_nid = s.wallet_nid
                    WHERE s.challenge_id = %s
                    ORDER BY s.submitted_on"""

        rs = cur.execute(query, (challenge_id, ))

        for row in cur.fetchall():
            wallet = Wallet.Wallet(row[8], row[7], row[6])
            wallet.nid = int(row[5])
            wallet.balance = decimal.Decimal(row[9])

            submission = Submission(int(row[1]), int(row[2]), wallet, row[10])
            submission.id = int(row[0])
            submission.submitted_on = int(row[4])

            submissions.append(submission)

        cur.close()
        conn.close()
        return submissions

    def get_wallet_by_nid(self, wallet_nid):
        w = None
        conn = self.connect()
        cur = conn.cursor()

        query = """SELECT
                 w.wallet_id,
                 w.wallet_nid,
                 w.wallet_name,
                 w.wallet_key,
                 wb.wallet_balance
                 FROM wallets w
                 JOIN wallet_balances wb ON wb.wallet_nid = w.wallet_nid
                 WHERE w.wallet_nid = %s"""

        result = cur.execute(query, (wallet_nid,))

        row = cur.fetchone()
        if row:
            w = Wallet.Wallet(row[2], row[3], row[0])
            w.nid = int(row[1])
            w.balance = decimal.Decimal(row[4])

        cur.close()
        conn.close()

        return w

    def get_wallet_by_id(self, wallet_id):
        w = None
        conn = self.connect()
        cur = conn.cursor()

        query = """SELECT
                 w.wallet_id,
                 w.wallet_nid,
                 w.wallet_name,
                 w.wallet_key,
                 wb.wallet_balance
                 FROM wallets w
                 JOIN wallet_balances wb ON wb.wallet_nid = w.wallet_nid
                 WHERE w.wallet_id = %s"""

        result = cur.execute(query, (wallet_id,))

        row = cur.fetchone()
        if row:
            w = Wallet.Wallet(row[2], row[3], row[0])
            w.nid = int(row[1])
            w.balance = decimal.Decimal(row[4])

        cur.close()
        conn.close()

        return w

    def get_wallet_by_address(self, wallet_address):  # todo rework this
        w = None
        conn = self.connect()
        cur = conn.cursor()

        if wallet_address.is_alias():
            query = """SELECT
                w.wallet_id,
                w.wallet_nid,
                w.wallet_name,
                w.wallet_key,
                wb.wallet_balance
                FROM wallets w
                JOIN wallet_aliases wa ON wa.wallet_nid = w.wallet_nid
                JOIN wallet_balances wb ON wb.wallet_nid = w.wallet_nid
                WHERE wa.alias = %s"""

            result = cur.execute(query, (wallet_address.alias(),))
        else:
            query = """SELECT
                w.wallet_id,
                w.wallet_nid,
                w.wallet_name,
                w.wallet_key,
                wb.wallet_balance
                FROM wallets w
                JOIN wallet_balances wb ON wb.wallet_nid = w.wallet_nid
                WHERE w.wallet_id = %s"""

            result = cur.execute(query, (wallet_address.alias(),))

        row = cur.fetchone()
        if row:
            w = Wallet.Wallet(row[2], row[3], row[0])
            w.nid = int(row[1])
            w.balance = decimal.Decimal(row[4])

        cur.close()
        conn.close()

        return w

    def add_wallet_balance(self, wallet):
        conn = self.connect()
        cur = conn.cursor()

        query = """INSERT INTO wallet_balances (wallet_nid, wallet_balance) VALUES (%s, %s)"""
        result = cur.execute(
            query, (wallet.nid, "{0:.5f}".format(
                wallet.balance),))

        conn.commit()
        cur.close()
        conn.close()

    def get_wallet_balance(self, wallet_nid):
        balance = decimal.Decimal(0)
        conn = self.connect()
        cur = conn.cursor()

        query = """SELECT wallet_balance FROM wallet_balances WHERE wallet_nid = %s"""

        result = cur.execute(query, (wallet_nid, ))

        row = cur.fetchone()
        if row:
            balance = decimal.Decimal(row[0])

        cur.close()
        conn.close()

        return balance

    def update_wallet_balance(self, wallet):
        conn = self.connect()
        cur = conn.cursor()

        query = """UPDATE wallet_balances SET wallet_balance = %s WHERE wallet_nid = %s"""
        result = cur.execute(
            query, ("{0:.5f}".format(
                wallet.balance), wallet.nid,))

        conn.commit()
        cur.close()
        conn.close()

    def get_transactions(self, start=0, count=100):
        transactions = []

        conn = self.connect()
        cur = conn.cursor()
        query = """SELECT transaction_id, source, recipient, amount, created_on, signature FROM transactions LIMIT %s, %s"""

        result = cur.execute(query, (start, count,))

        rows = cur.fetchall()
        for row in rows:
            t = Transaction.Transaction(row[0], row[1], row[2], row[3], row[4])
            t.signature = row[5]
            transactions.append(t)

        return transactions

    def create_transaction(self, transaction):
        timestamp = int(time.time())
        conn = self.connect()
        cur = conn.cursor()
        query = """INSERT INTO transactions (source, recipient, amount, created_on, signature) VALUES (%s, %s, %s, %s, %s)"""

        result = cur.execute(
            query,
            (transaction.source,
             transaction.recipient,
             "{0:.5f}".format(
                 transaction.amount),
                timestamp,
                transaction.signature))

        # fetching the id

        query = """SELECT transaction_id FROM transactions WHERE source = %s AND recipient = %s AND amount = %s AND created_on = %s"""

        result = cur.execute(
            query,
            (transaction.source,
             transaction.recipient,
             "{0:.5f}".format(
                 transaction.amount),
                timestamp,
             ))

        conn.commit()

        row = cur.fetchone()

        transaction.id = int(row[0])

        cur.close()
        conn.close()

    def create_wallet(self, wallet):
        conn = self.connect()

        timestamp = int(time.time())
        cur = conn.cursor()
        query = """INSERT INTO wallets (wallet_id, wallet_name, wallet_key, created_on) VALUES (%s, %s, %s, %s)"""

        result = cur.execute(
            query, (wallet.id, wallet.name, wallet.key, timestamp,))

        conn.commit()
        # fetching the nid

        query = """SELECT wallet_nid FROM wallets WHERE wallet_id = %s AND created_on = %s"""

        result = cur.execute(query, (wallet.id, timestamp,))

        row = cur.fetchone()

        wallet.nid = row[0]

        cur.close()
        conn.close()

    def get_wallets(self, start=0, count=100):
        wallets = []
        end = start + count
        conn = self.connect()
        cur = conn.cursor()

        query = """SELECT wallet_nid, wallet_id, wallet_name, wallet_key FROM wallets LIMIT %s, %s"""
        result = cur.execute(query, (start, end,))

        rows = cur.fetchall()

        for row in rows:
            w = Wallet.Wallet(row[2], row[3], row[1])
            w.nid = row[0]
            wallets.append(w)

        cur.close()
        conn.close()

        return wallets
