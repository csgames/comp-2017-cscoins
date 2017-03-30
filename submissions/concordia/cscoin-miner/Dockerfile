FROM jimmycuadra/rust:1.16.0
COPY ./CSCoins /CSCoins
COPY ./cscoins /cscoins
WORKDIR /CSCoins/cscoin-miner
ENTRYPOINT ["/bin/bash", "-c", "cargo run --release"]
