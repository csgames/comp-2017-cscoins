# Important!

This document might still be updated until the beginning of the CS Games 2017. We recommend that interested parties watch the [https://github.com/csgames/cscoins](https://github.com/csgames/cscoins) repository to be notified as soon as a new change is introduced. For any issue, bug or needed clarification, please open an issue in the GitHub project.

This repository contains the CSCoin specification and the source code for the Central Authority server. More samples should be added in the near future to manage a CSCoin wallet and a (slow) reference implementation for a miner.

Enjoy!

# CSCoins Documentation

## Summary

The Pre-CS Games challenge is a new concept for the [CS Games 2017](http://2017.csgames.org/) proposing a competition that teams can work on before the CS Games. This competition should still be doable in the span of the week-end for late teams and a minimal PoC will be available. During the week-end, points will be awarded to the best miners as part of the Puzzle Hero challenge.

The concept is to create a nano-economy for the CS Games event through the implementation of a [cryptocurrency](https://en.wikipedia.org/wiki/Cryptocurrency) called "CSCoins". Therefore, teams will have to develop a miner to mine and get CSCoins for the week-end. The team will then be able to spend the coins in exchange of goods, hints and extra points! The CSCoins is a currency exclusively for the CS Games 2017 week-end and only blocks mined during the event can be used for trading. Teams are still encouraged to start mining beforehand to properly test their miner!

CSCoins are a currency gained by solving a challenge.  Unlike distributed peer-to-peer currencies such as [Bitcoin](https://en.wikipedia.org/wiki/Bitcoin), a server authority hosted by the organization committee will handle the challenge distribution and synchronization between all peers. The server authority will be proposing a challenge to be solved and awarding CSCoins for the first miner's wallet to solve it, after which a new challenge will be proposed.

## Contents

*   [Pseudo Random Number Generator](#random-number-generator)
*   [The challenge](#challenge)
*   [Challenge Type](#challenge-type)
*   [Wallet](#wallet)
*   [Message Signature](#message-signature)
*   [Communication with the Central Authority](#communication-with-ca)

## Pseudo Random Number Generator

All challenges require the miners to generate random data from a given seed. In order to generate the same random number on each computer for a given seed, the same [pseudorandom number generator](https://en.wikipedia.org/wiki/Pseudorandom_number_generator) has to be used by all the teams and the Central Authority. The used PRNG is the [Mersenne Twister (MT19937-64)](https://en.wikipedia.org/wiki/Mersenne_Twister). Implementations are freely available on the internet and in most standard libraries.

## The Challenge

The challenge is about finding a SHA256 hash that matches the target prefix given by the Central Authority. All previous solutions are also included into the current solution.

When a miner fetches the current challenge from the Central Authority, a challenge name will specify which problem needs to be solved. For example, the server will tell the miner to solve the `"sorted_list"` challenge type.

Along with the challenge name, the Central Authority server might also specify additional parameters for the challenge. For example, the sorted list challenge will have the `"nb_elements"` parameter. This parameter will tell the miner how many numbers need to be generated for the challenge.

Once the miner has the challenge parameters, it can start generating the challenge dataset. It does so by generating `nb_elements` 64 bits unsigned integer with the Pseudo Random Number Generator. The seed state used by the PRNG is the first 8 bytes of the SHA256 Hash of the concatenation of the last solution hash (in stringified hex) and a given nonce (`SHA256(HEX(LastSolutionHash) | Nonce)[:8]`).

Once the challenge dataset is generated, the miner has to solve the challenge. In the sorted list challenge, it must sort the elements to generate a solution string. To build that string, the miner has to put all values of the list in sorted order, convert them to their string representation (in base 10) and concatenate them together.
**Example**: Given a list of 5 numbers, `[9, 4, 5, 9, 2]`. The sorted list solution string is: `"24599"`.

Finally, the solution string is hashed with SHA256 and the result compared to the prefix provided by the Central Authority server. If it does match, the miner can submit the nonce used to generate the challenge and get awarded a CSCoin!

Otherwise, the miner needs to try again with a new random nonce, generate a new challenge dataset, sort it, and keep trying until a solution hash matches the wanted prefix.
### Example

The miner starts by requesting the current challenge properties from the Central Authority. It gives it the first challenge:
```json
{
    "challenge_id": 0,
    "challenge_name": "sorted_list",
    "last_solution_hash": "0000000000000000000000000000000000000000000000000000000000000000",
    "hash_prefix": "94f9",
    "parameters": {
        "nb_elements": 20
    }
}
```

This is the first challenge of the blockchain, so the last solution hash is `"0..0000"`. We can try our first mining attempts with a nonce set to `"0"`.

So we hash `"00000000000000000000000000000000000000000000000000000000000000000"` (`'0'` x 65). Which give us the hex digest: `e531ef0f962409170917abf9de3287afec23dd1c42c9e1fea66c5feab99e8f7c`.

We use the first 8 bytes to generate an integer, this integer will be our seed number. `"\xe5\x31\xef\x0f\96\x24\x09\x17"` or `0x170924960fef31e5` as an unsigned 64 bits integer.

With the seeded Mersenne Twister PRNG, generate 20 unsigned 64 bits random integer:
```json
[187434852114612846, 10837196899528407950, 13231065775368684808, 4942314897761499926, 17028306872668076666, 6479076410078001012, 1361812409744256450, 3291217005668754618, 4966164133636131008, 7642938895213376385, 2143391747588726128, 10354190044461362030, 7773684818964863771, 10794580392141786114, 16492712020482564264, 9905729874405870466, 5103580236542799915, 15262620284228700467, 4872192301904809974, 2466619936935862033]
```

We order them:
```json
[187434852114612846, 1361812409744256450, 2143391747588726128, 2466619936935862033, 3291217005668754618, 4872192301904809974, 4942314897761499926, 4966164133636131008, 5103580236542799915, 6479076410078001012, 7642938895213376385, 7773684818964863771, 9905729874405870466, 10354190044461362030, 10794580392141786114, 10837196899528407950, 13231065775368684808, 15262620284228700467, 16492712020482564264, 17028306872668076666]
```

We build the solution string by concatenating those numbers together:
```json
"18743485211461284613618124097442564502143391747588726128246661993693586203332912170056687546184872192301904809974494231489776149992649661641336361310085103580236542799915647907641007800101276429388952133763857773684818964863771990572987440587046610354190044461362030107945803921417861141083719689952840795013231065775368684808152626202842287004671649271202048256426417028306872668076666"
```

We finally hash this solution string to know if it matches the challenge hash prefix: `e9528071d01ab08cc4c9e74fee45df95af0256a469f17aa88918dc14a4008eb7`

`e952` != `94f9`, So we need to try again. We generate a new random nonce and reseed the random number generator.

Our new random nonce is `"96436717027"`.

So we hash `"000000000000000000000000000000000000000000000000000000000000000096436717027"`. Which give us: `b998963f3add4b84a5bb2b28bff28e2c556cb860e73d110679b5f9c2ac65bad4`

`\xb9\x98\x96\x3f\x3a\xdd\x4b\x84` or `0x844bdd3a3f9698b9` as 64 bits integer.

Our new numbers are:
```json
13916525834144929239, 14267992374683960415, 17447482481089031970, 17757524129420908411, 3262888185675309556, 4651484254165491713, 14892328834357397553, 642435218906306919, 12375157785219615227, 17110841558370943827, 17014653408604181717, 16941248359459129302, 448482909903223685, 13547565333399307760, 7472403995188135213, 7093177824549920619, 4562417252290276756, 17541524771507166271, 10898898378669729391, 9285048143772460569
```

The numbers are sorted and the solution string becomes:
```json
"448482909903223685642435218906306919326288818567530955645624172522902767564651484254165491713709317782454992061974724039951881352139285048143772460569108988983786697293911237515778521961522713547565333399307760139165258341449292391426799237468396041514892328834357397553169412483594591293021701465340860418171717110841558370943827174474824810890319701754152477150716627117757524129420908411"
```
Hashing the solution string yields the digest: `90c7e5020a21158beeaabe40d1c736aae12006cf7e42e54ade214aa0d117f76f`. Still not matching 94f9...

Let's keep trying.

Nonce: `"81784174387"`
Solution string:
```json
"14613756414282971623351850839923216032604591025189233583278004316398116031737494204873404157097956175972540962389795776429494244233386458705439214184388772978573088406573977918510034278539512326892073404680294124473732129277028371274333156794756411413874379310994180637141008807081214681961440775241872191186315042601059964403280159044527214885406591646714127635125464218076835083475092149"
```

Solution Hash: `94f983bf4d2e06610db4f15bfc6237f5d9e5f79a2e9502e52cd0ddfca905b163`. The first bytes match `94f9`!

So we can submit the nonce to the Central Authority Server and win more CSCoins!

A new challenge is then generated. The miner fetches the updated information from the server:
```json
{
    "challenge_id": 0,
    "challenge_name": "sorted_list",
    "last_solution_hash": "94f983bf4d2e06610db4f15bfc6237f5d9e5f79a2e9502e52cd0ddfca905b163",
    "hash_prefix": "9098",
    "parameters": {
        "nb_elements": 20
    }
}
```


This is the second challenge, so the miner now has the previous hash to seed the PRNG. We hash the last solution and a random nonce to seed the PRNG: `SHA256("94f983bf4d2e06610db4f15bfc6237f5d9e5f79a2e9502e52cd0ddfca905b163" + "248565")`. This gives us the digest: `83d51291b621b0a96c6a871256c911ca431b1ff24102f069951659457cb0d8fb`.

We use the first 8 bytes to generate a 64 bits unsigned integer, this integer will be our seed number: `\x83\xd5\x12\x91\xb6\x21\xb0\xa9` or `0xa9b021b69112d583`.

We use the seeded PRNG to generate 20 random 64 bits unsigned integers:

```json
7554992472722769382, 8495646299498670407, 16283171823286969215, 14362607901913361150, 6692862674045639924, 9015192917032127462, 327830662700023863, 9371480197312631464, 16474393573432639799, 11349000119560803050, 3722572335198690747, 11617180555990659053, 14400604751394908311, 16917897951851071986, 4035298408703112487, 5375153024761395986, 1544660713920769741, 16852903019784931493, 16173382640596610454, 17545493636135106882
```

We order them:
```json
327830662700023863, 1544660713920769741, 3722572335198690747, 4035298408703112487, 5375153024761395986, 6692862674045639924, 7554992472722769382, 8495646299498670407, 9015192917032127462, 9371480197312631464, 11349000119560803050, 11617180555990659053, 14362607901913361150, 14400604751394908311, 16173382640596610454, 16283171823286969215, 16474393573432639799, 16852903019784931493, 16917897951851071986, 17545493636135106882
```

We build the solution string by concatenating those numbers together:
```json
32783066270002386315446607139207697413722572335198690747403529840870311248753751530247613959866692862674045639924755499247272276938284956462994986704079015192917032127462937148019731263146411349000119560803050116171805559906590531436260790191336115014400604751394908311161733826405966104541628317182328696921516474393573432639799168529030197849314931691789795185107198617545493636135106882
```

We hash the solution: `7d5fb906c70df5d43275e30bb044f64fbd5b4c2a2c8a92597700c7d1709a202b`.

Not matching the `9098` prefix sent by the Central Authority server...

We keep trying with new random nonce.

Nonce: `814267888`
Seed: `\x1e\xcd\xad\x5d\xa4\x6f\x9c\xd1`
Solution String:
```json
14972298174551654431723443700797644249245561621187992295327772395864560490123211875208621964684366752263225374374359043564571525613596800776372508179546694401260438463381870003110298946106127394782186625229873765168077041493964789015194588102489029158224598323790499101425615433341222851103238794091706851112945981076343021800175517732451163502481827820657423093272318368446283940966322
```

We hash the solution: `90985e24a9e0b8ece598cf643e303424ae5d1c3f5a9903c08f1dcd3b8e1a3454`.
Matching the prefix sent by the Central Authority server.

How lucky we are, another CSCoin awarded to our wallet. That's pretty much what mining is about. Generate a challenge dataset, solve it and check if the solution hash is valid. Rinse and repeat!

## Challenge Type

### Sorted List

This challenge is simple and yet offers many ways to the miners to optimize their processing. The challenge begins by generating 64 bits unsigned integers from the PRNG. Afterward the miner has to sort all the numbers to hash the solution.

**Challenge Name**: `sorted_list`
**Parameters**:
 * **nb_elements**: Number of integer to generate and sort.

**Solution String Formatting**: Convert all integers into their decimal string representation and join all together without any whitespaces.

**Example**: Given the numbers `[400, 2, 4, 3, 5]`, the solution string would be `"2345400"`.

#### Reverse Sorted List


Just like the Sorted List challenge, this challenge begins by generating 64 bits unsigned integers from the PRNG. Afterward the miner has to sort all the numbers in **descending order** to hash the solution.

**Challenge Name**: `reverse_sorted_list`
**Parameters**:
 * **nb_elements**: Number of integer to generate and sort.

**Solution String Formatting**: Convert all integers into their decimal string representation and join all together without any whitespaces.

**Example**: Given the numbers `[400, 2, 4, 3, 5]`, the solution string would be `"4005432"`.

## Wallet

A wallet is a RSA key pair of 1024 bits. To send or receive coins, we use the Wallet Id. The Wallet Id is a SHA256 Hash of a client public key in DER ([Distinguished Encoding Rules](https://en.wikipedia.org/wiki/X.690#DER_encoding)) format.

A client needs its private key to sign the submission message and create a transaction message to prove that it is the owner of the wallet.

A client will need to register its public key on the Central Authority Server to be able to do submission and create a transaction.

To calculate a client's Wallet balance, a client needs to retrieve all the transactions and compute the transaction outcomes.

### Message Signature

We are using RSA digital signature protocol according to PKCS#1 v1.5. Some messages required a signature to validate that the client is the owner of the wallet. Usually, the signed contents are the arguments of the command, joined together by a comma (`,`). A signature is always represented in a stringified hexadecimal format. The Central Authority server will validate the signature against the registered public key by the client.

### Communication with the Central Authority

The Central Authority Server use the [WebSocket protocol](https://en.wikipedia.org/wiki/WebSocket) to communicate. The server URI is [wss://cscoins.2017.csgames.org:8989/client](wss://cscoins.2017.csgames.org:8989/client). Once a client is connected, the server will be waiting for any incoming commands. All data sent or received are serialized in JSON.

### Available commands

*   [get_current_challenge](#get-current-challenge-command)
*   [get_challenge_solution](#get-challenge-solution-command)
*   [close](#close-command)
*   [register_wallet](#register-wallet-command)
*   [get_transactions](#get-transactions-command)
*   [create_transaction](#create-transaction-command)
*   [submission](#submission-command)
*   [ca_server_info](#ca-server-info-command)

#### Command object

|Field Name|Type|Description|
|----------|----|-----------|
|command|String|The name of the command. **Example**: `get_challenge_solution`|
|args|Dictionary&lt;String, Object&gt;|Parameters for the command, see each command's documentation|

#### Get Current Challenge

Fetch the current problem set from the Central Authority. 

After the first call of this command, you will automatically receive the new challenge when it's available, until the connection is closed.

**Command Name:** get_current_challenge

##### Argument(s)

There's no argument.

##### Response

|Field Name|Type|Description|
|----------|----|-----------|
|time_left|Integer|Time left in seconds to solve the problem set.|
|challenge_id|Integer|Current challenge id|
|challenge_name|String|Current challenge type name. **Example**: `sorted_list`|
|hash_prefix|String|Solution hash prefix used to validate a solution hash. The prefix is represented in a hexadecimal string format. **Example**: `a4f1`|
|last_solution_hash|String|Last valid solution hash. Must be used as part of the seed for the current challenge. **Example**: `30fe523cb3c9007b50242736a8a099215e6ea533f3c8012c9dac34756257d6dc`|
|parameters|Dictionary&lt;String, Object&gt;|Parameters of the challenge, they are specific to the challenge type. See the Challenge Type section for more details.|

#### Get previous solutions

Fetch the solution of a challenge

**Command Name:** get_challenge_solution

##### Argument(s)

|Field Name|Type|Description|
|----------|----|-----------|
|challenge_id|Integer|Challenge id for which a solution is requested.|

##### Response

The response has the same content as the `get_current_challenge` command, with the addition of those two fields:

|Field Name|Type|Description|
|----------|----|-----------|
|nonce|String|Nonce used to seed the PRNG.|
|solution_hash|String|Solution hash that validated with the challenge prefix.|

#### Close connection

Close the connection with the Central Authority Server

**Command Name**: close

##### Argument(s)

There's no argument.

##### Response

There's no response.

#### Register a new Wallet

Register your Wallet's public key with the Central Authority.

**Command Name**: register_wallet

##### Argument(s)

|Field Name|Type|Description|
|----------|----|-----------|
|name|String|Your Wallet Name, you should use your Team Name here.|
|key|String|Your wallet's public key, in [PEM](https://en.wikipedia.org/wiki/Privacy-enhanced_Electronic_Mail) format.|
|signature|String|[Message signature](#message-signature) in hexadecimal format. The signed message used is the `wallet_id` being registered.|

##### Response

|Field Name|Type|Description|
|----------|----|-----------|
|error|String|Error message if something went wrong|

#### Get Transactions

Get transactions history from the Central Authority.

**Command Name**: get_transactions

##### Argument(s)

|Field Name|Type|Description|
|----------|----|-----------|
|start|Integer|Starting index of the requested transactions.|
|count|Integer|Number of transaction requested.|

##### Response

|Field Name|Type|Description|
|----------|----|-----------|
|error|String|Error message if something went wrong|
|transactions|Array&lt;Transaction&gt;|List of transaction(s)|

##### Transaction Object

|Field Name|Type|Description|
|----------|----|-----------|
|id|Integer|Transaction id|
|source|String|Source Wallet id|
|recipient|String|Recipient Wallet id|
|amount|Decimal|Transaction amount|

#### Create a new Transaction (Send coins)

Create a new Transaction, sending coins to another wallet

**Command Name**: create_transaction

##### Argument(s)

|Field Name|Type|Description|
|----------|----|-----------|
|source|String|Source Wallet id|
|recipient|String|Recipient Wallet id|
|amount|Decimal|Amount to send, Minimum 0.00001.|
|signature|String|[Message Signature](#message-signature) in hexadecimal format. The signed message is `source,recipient,amount`. The amount is a decimal number formatted with 5 digit of precision. **Example**: `amount` = 2, would be written as `2.00000` in the message. The signature must be validated by the public key related to the source Wallet id.|

##### Response

|Field Name|Type|Description|
|----------|----|-----------|
|error|String|Error message if something went wrong.|
|id|Integer|New transaction id.|

#### Submit a problem solution

Submit a solution for the current challenge, awarding CSCoins to the miner if the solution is valid.

**Command Name**: submission

##### Argument(s)

|Field Name|Type|Description|
|----------|----|-----------|
|wallet_id|String|Miner Wallet id.|
|nonce|String|Nonce used to find a valid solution hash.|

##### Response

|Field Name|Type|Description|
|----------|----|-----------|
|error|String|Error message if something went wrong.|

#### Get Central Authority Server Information

Fetch the current information of the Central Authority server

**Command Name**: ca_server_info

##### Argument(s)

There's no argument.

##### Response

|Field Name|Type|Description|
|----------|----|-----------|
|minutes_per_challenge|Integer|Maximum time of a challenge in minutes.|
|coins_per_challenge|Integer|Coins awarded for a valid submission.|
|min_transaction_amount|Decimal|Minimum transaction amount.|
|ca_public_key|String|Central Authority PublicKey in ([PEM](https://en.wikipedia.org/wiki/Privacy-enhanced_Electronic_Mail)) format.|
