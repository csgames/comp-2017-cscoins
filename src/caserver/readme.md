#### Central Authority Server

### D�pendances

 * Python 3.5 et +
 * Websockets
 * asyncio
 * mysqlclient
 * pycrypto
 * numpy

### TO DO
 - [ ] D�finir l'augmentation de difficult� dynamique
 - [ ] Fournir une API pour faire un tableau de bord, pour afficher le nombre de coins distribu�s et d'autres statistique.
 - [ ] Logger
 - [ ] Nettoyage des connexions


### Infra
  * Tester sur debian testing (stretch). Version de Python3 pas assez récentes
  * Les VM miners devraient aussi être sur Debian Stretch, avec les même packages plus : build-essential, git
  * packages nécessaires : python3-pip, mysql-server, libmysqlclient, libmysqlclient-dev, mysql-utilities
  * packages pip : websockets, asyncio, mysqlclient, pycrypto (pip3 install)
