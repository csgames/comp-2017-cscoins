# CONCORDIA UNIVERSITY - CSGames 2017 - CSCoins submission

## CSCoin Miner

Our CSCoin miner was written in the [Rust](https://www.rust-lang.org/en-US/) programming language.

It's using a binary heap to incremently sort the lists, and returns the lists reversed or in order based on the argument.

The shortest list challenges uses a Dijkstra algorithm implementation.

Our program is multithreaded, and deploys 8 threads that accumulate answers. After a chunk of results have been inserted in a rust vec, they are verified, in a way as to be vectorized by the rust compiler.

All mining is implemented by the Miner module, which is used by the Thread module, which creates threads, each containing a miner, which try to find solutions until they receive a stop commmand.

The assignments and commands are provided by the Comm module, which communicates with the central server.


## Deployment

Our entire program can be build using `cargo run --release`.

## Docker Deployment

We've created a Dockerfile in order to successfully deploy our application to the provided Docker host. We've included the all necessary files with some private information redacted.

Some sample commands for our Docker deployment are shown below.
```
source /home/amir/github/cscoins/docker-client/env.rc
sudo docker --config /home/amir/github/cscoins/docker-client/ build . -t concordia_miner
sudo docker --config /home/amir/github/cscoins/docker-client/ create concordia_miner
sudo docker --config /home/amir/github/cscoins/docker-client/ start ###container###
```
