#
# CS Coins central server
# 
import os
import sys
sys.path.append('..')

import CentralAuthorityServer

if __name__ == "__main__":
    ca_server = CentralAuthorityServer.CentralAuthorityServer()
    ca_server.serve()
