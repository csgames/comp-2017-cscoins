import decimal
import time


class WalletDistribution:
    def __init__(self, id_prefix, coin_value):
        self.id_prefix = id_prefix
        self.coin_value = coin_value


class DistributionStatistic:
    def __init__(self, coins_distributed, possible_coins, wallet_distributions=[]):
        self.coins_distributed = coins_distributed
        self.possible_coins = possible_coins
        self.wallet_distributions = wallet_distributions


class ServerStatistic:
    def __init__(self):
        self.distributions = []
        self.start_time = time.time()
        self.submissions_count = 0

    def uptime(self):
        return int(time.time() - self.start_time)
