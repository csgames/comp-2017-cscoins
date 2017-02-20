#
# CS Coins central server
# 
import os
import sys
sys.path.append('..')

import CentralAuthorityServer

if __name__ == "__main__":
    # loading central authority key
    ca_key_file = "ca_key.txt"

    if not os.path.exists(ca_key_file):
        print("Central Authority key not found !")
        print("Exiting...")
        sys.exit(-1)

    ca_server = CentralAuthorityServer.CentralAuthorityServer()
    ca_server.serve()
