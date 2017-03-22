CS Coins Miners environment
===================

To mine our new crypto-currency, we give you an environment to run your miner. This environment is running on Docker. We're using a Docker proxy to allow a minimal subset of command. The Docker Host is running at `miners.2017.csgames.org`. Each University will be allowed to run one container on the Docker Host.

### How to communicate with the Docker Host

You need docker-cli installed on your computer to access the docker host.
You need to source `env.rc` and edit the secret token in `config.json`. 
Each University will receive a secret token to communicate with the Docker Host. This token will determine your container name.

Five commands are available through our proxy :

 - **build** : to build your Docker Image, your image name will be forced tagged with your university name.
 - **create** : this will create a new container with the lastest image you've build. Again, the name of the container will be forced by our proxy.
 - **start** : to start your container.
 - **rm** : to delete your container.
 - **logs** : to see your container process StdOut and StdErr.
 
For more information about the command, you can visit the [Docker command documentation](https://docs.docker.com/engine/reference/commandline/docker/#child-commands)

### Setup procedures

We're supposing that Docker client is already installed on your computer.

 1. Fetch `env.rc` and `config.json`. Put your secret token into `config.json`. After source the `env.rc` file.
    
	> $ source env.rc
	
	- The CA Certificate must be in ~/.cscert/ folder. Else, you'll need to modify `env.rc` with the path to the folder containing the `ca.pem` file.
	
 2. Create a new directory with a empty Dockerfile. Edit this Dockerfile, this file will tell to Docker what you need into your container. For more information, visit the [Dockerfile reference](https://docs.docker.com/engine/reference/builder/).
 
 3. Build your image with Docker. You also need to specify the path to the folder containing config.json, to inject the token into the header of the Docker query. We also need the path to the folder containing your Dockerfile.
 
    > $ docker --config path/to/config/folder/ build path/to/folder/containing/dockerfile/

    - This will build your image on the Docker host. You image will forced tagged with your university name.

 4. Create a new container. This will create a new container with the lastest version of your image. You need to specify a name, but that name will be overridden by our proxy.
  
    > $ docker --config path/to/config/folder/ create myminer

 5. Start your container. You also need to specify a container name in the arguments, but it will be overridden by our proxy.
 
    > $ docker --config /path/to/config/folder/ start myminer

 6. If you want to stop or update your container, you will need to delete it and return to step 3.
  
    > $ docker --config path/to/config/folder/ rm -f myminer
