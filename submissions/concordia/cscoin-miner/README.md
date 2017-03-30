# Docker

### Creating our Docker image
- remove your `target/` directory and any gzipped archives
```
cd cscoin-miner
rm -rf target/
rm cscoins-concordia.tar.gz
```
- pack our source code
```
tar -czvf cscoins-concordia.tar.gz .
```
- source our `env.rc` (:warning: Make sure the cert path is pointing to our repository :warning:)
```
source config/env.rc
```

- Build

```
sudo docker --config config build .
```

- Create

```
sudo docker --config config create myminer
```

- Start

```
sudo docker --config config start myminer
```

### OLD
```
sudo docker run --net=host --name cscoins-client -it cscoins-concordia-miner-test sh -c "cargo run --release"
```

