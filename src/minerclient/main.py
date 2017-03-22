import sys
sys.path.append('..')

import MinerClient
import asyncio

keys_dir = ""
wallet_name = "SimpleMiner"

ia = len(sys.argv)
i = 1

while i < ia:
    arg = sys.argv[i]
    if arg == '-k':
        if i + 1 < ia:
            keys_dir = sys.argv[i+1]
            i += 1
    elif arg == '-n':
        if i + 1 < ia:
            wallet_name = sys.argv[i+1]
            i += 1
    i += 1

mc = MinerClient.MinerClient(keys_dir, "cscoins.2017.csgames.org", wallet_name)
asyncio.get_event_loop().run_until_complete(mc.client_loop())
