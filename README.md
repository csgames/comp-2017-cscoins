# CSCoins Documentation

## Summary

The Pre-CS Games challenge is a new concept for the [CS Games 2017](http://2017.csgames.org/) proposing a competition involving the teams to work on it before the week-end of the CS Games. This competition should still be doable in the span of the week-end for the late teams and a minimal PoC will be available. During week-end, points will be awarded to the best miners as part of the Puzzle Heroes challenge.

The concept is to create a nano-economy for the CS Games event through the implementation of a [cryptocurrency](https://en.wikipedia.org/wiki/Cryptocurrency) called "CSCoins". Therefor, teams will have to develop a miner to mine and get CSCoins currency for the week-end. The team should then be able to spend the coins in exchange of goods, hints and extra points! The CSCoins is a currency exclusively for the CS Games 2017 week-end and only blocks mined for the event will be used for trading. Team are still encouraged to start mining beforehand to properly test their miner!

CS Coins are a currency gained by solving a challenge.  Unlike distributed peer-to-peer currencies such as [Bitcoin](https://en.wikipedia.org/wiki/Bitcoin), a server authority hosted by the organisation committee will handle the challenge distribution and synchronisation between all peers. The server authority will be proposing a challenge to be solved and awarding CSCoins for the first miner's wallet to solve it, after which a new challenge will be proposed.

## Contents

*   [Pseudo Random Number Generator](#random-number-generator)
*   [The challenge](#challenge)
*   [Challenge Type](#challenge-type)
*   [Wallet](#wallet)
*   [Message Signature](#message-signature)
*   [Communication with the Central Authority](#communication-with-ca)

## Pseudo Random Number Generator

All challenges require the miners to generate random data from a given seed. In order to generate the same random number on each computers for a given seed, the same [pseudorandom number generator](https://en.wikipedia.org/wiki/Pseudorandom_number_generator) have to be used by all the teams and the Central Authority. The used PRNG is the [Mersenne Twister (MT19937-64)](https://en.wikipedia.org/wiki/Mersenne_Twister). Many implementations are freely available on internet and most standard library.

## The Challenge

The challenge is about finding a SHA256 hash that is matching the target prefix given by the Central Authority. All previous solutions are also included into the current solution.

When a miner fetch the current challenge from the Central Authority, a challenge name will specify which problem needs to be solved. For example, the server will tell the miner to solve the `"sorted_list"` challenge type.

Along with the challenge name, the Central Authority server might also specify additonnals parameters for the challenge. For example, the sorted list challenge will have the `"nb_elements"` parameter. This parameters will tell the miner how many numbers need to be generated for the challenge.

Once the miner has the challenge parameters, it can start generating the challenge dataset. It does so by generating `nb_elements` 64 bits unsigned integer with the Pseudo Random Number Generator. The seed state used by the PRNG is the first 8 bytes of the SHA256 Hash of the concatenation of the last solution hash (In stringified hex) and a given nonce (`SHA256(HEX(LastSolutionHash) | Nonce)[:8]`).

Once the challenge dataset is generated, the miner has to solve the challenge. In the case of the sorted list challenge, it must sort the elements to generate a solution string. To build that string, the miner has to put all values of the list in sorted order, the number are then converted to their string represented in base 10 and concatenated together.
**Example**: Given a list of 5 numbers, `[9, 4, 5, 9, 2]`. The sorted list solution string is: `"24599"`. 

Finally, the solution string is hashed with SHA256 and the result compared to the prefix provided by the Central Authority server. If it does match, the miner can submit the nonce used to generate the challenge and get awarded a CSCoin!

Else the miner need to try again with a new random nonce, regenerating a new challenge dataset, sort it, and keep trying until a solution hash match the wanted prefix.

### Example

The miner start by requesting the current challenge properties from the the Central Authority. It gives it the first challenge:
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

This is the first challenge of the blockchain, so the last solution hash is `"0..0000"`. We can try our first mining attemps with a nonce set to `"0"`.

So we hash `"00000000000000000000000000000000000000000000000000000000000000000"` (`'0'` x 65). Which give us the hex digest: `e531ef0f962409170917abf9de3287afec23dd1c42c9e1fea66c5feab99e8f7c`. 

We use the last 8 bytes to generate an integer, this integer will be our seed number. `"\xe5\x31\xef\x0f\96\x24\x09\x17"` or `0x170924960fef31e5` as an unsigned 64 bits integer. 

With the seeded Mersenne Twister PRNG, generate 20 unsigned 64 bits random integer: 
```json
[187434852114612846, 10837196899528407950, 13231065775368684808, 4942314897761499926, 17028306872668076666, 6479076410078001012, 1361812409744256450, 3291217005668754618, 4966164133636131008, 7642938895213376385, 2143391747588726128, 10354190044461362030, 7773684818964863771, 10794580392141786114, 16492712020482564264, 9905729874405870466, 5103580236542799915, 15262620284228700467, 4872192301904809974, 2466619936935862033]
```

We order them :
```json
[187434852114612846, 1361812409744256450, 2143391747588726128, 2466619936935862033, 3291217005668754618, 4872192301904809974, 4942314897761499926, 4966164133636131008, 5103580236542799915, 6479076410078001012, 7642938895213376385, 7773684818964863771, 9905729874405870466, 10354190044461362030, 10794580392141786114, 10837196899528407950, 13231065775368684808, 15262620284228700467, 16492712020482564264, 17028306872668076666]
```

We build the solution string by concatenating those numbers together : 
```json
"18743485211461284613618124097442564502143391747588726128246661993693586203332912170056687546184872192301904809974494231489776149992649661641336361310085103580236542799915647907641007800101276429388952133763857773684818964863771990572987440587046610354190044461362030107945803921417861141083719689952840795013231065775368684808152626202842287004671649271202048256426417028306872668076666"
```

We finally hash this solution string to know if it matches the challenge hash prefix: `e9528071d01ab08cc4c9e74fee45df95af0256a469f17aa88918dc14a4008eb7`

`e952` != `94f9`, So we need to try again. We generate a new random nonce, reseed the random number generator.

Our new random nonce is `"96436717027"`.

So we hash `"000000000000000000000000000000000000000000000000000000000000000096436717027"`. Which give us: `b998963f3add4b84a5bb2b28bff28e2c556cb860e73d110679b5f9c2ac65bad4`

`\xb9\x98\x96\x3f\x3a\xdd\x4b\x84` or `0x844bdd3a3f9698b9` as 64 bits integer. 

Our new numbers are : 
```json
13916525834144929239, 14267992374683960415, 17447482481089031970, 17757524129420908411, 3262888185675309556, 4651484254165491713, 14892328834357397553, 642435218906306919, 12375157785219615227, 17110841558370943827, 17014653408604181717, 16941248359459129302, 448482909903223685, 13547565333399307760, 7472403995188135213, 7093177824549920619, 4562417252290276756, 17541524771507166271, 10898898378669729391, 9285048143772460569
```

The numbers are sorted and the solution string become:
```json
"448482909903223685642435218906306919326288818567530955645624172522902767564651484254165491713709317782454992061974724039951881352139285048143772460569108988983786697293911237515778521961522713547565333399307760139165258341449292391426799237468396041514892328834357397553169412483594591293021701465340860418171717110841558370943827174474824810890319701754152477150716627117757524129420908411"
```
Hashing the solution string yield the digest: `90c7e5020a21158beeaabe40d1c736aae12006cf7e42e54ade214aa0d117f76f`. Still not matching 94f9...

Let's keep trying.

Nonce: `"81784174387"`
Solution string:
```json
"14613756414282971623351850839923216032604591025189233583278004316398116031737494204873404157097956175972540962389795776429494244233386458705439214184388772978573088406573977918510034278539512326892073404680294124473732129277028371274333156794756411413874379310994180637141008807081214681961440775241872191186315042601059964403280159044527214885406591646714127635125464218076835083475092149"
```

Solution Hash: `94f983bf4d2e06610db4f15bfc6237f5d9e5f79a2e9502e52cd0ddfca905b163`. The first bytes matches `94f9`!

So we can submit the nonce to the Central Authority Server and win more CSCoins!

A new challenge is then generated. The miner fetch the updated information from the server:
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


This is the second challenge, so the miner now have the previous hash to seed the PRNG. We hash the last solution and a random nonce to seed the PRNG: `SHA256("94f983bf4d2e06610db4f15bfc6237f5d9e5f79a2e9502e52cd0ddfca905b163" + "248565")`. This give use the digest: `83d51291b621b0a96c6a871256c911ca431b1ff24102f069951659457cb0d8fb`. 

We use the first 8 bytes to generate an 64 bits unsigned integer, this integer will be our seed number: `\x83\xd5\x12\x91\xb6\x21\xb0\xa9` or `0xa9b021b69112d583`. 

We use the seeded PRNG to generate 20 random 64 bits unsigned integers:

```json
7554992472722769382, 8495646299498670407, 16283171823286969215, 14362607901913361150, 6692862674045639924, 9015192917032127462, 327830662700023863, 9371480197312631464, 16474393573432639799, 11349000119560803050, 3722572335198690747, 11617180555990659053, 14400604751394908311, 16917897951851071986, 4035298408703112487, 5375153024761395986, 1544660713920769741, 16852903019784931493, 16173382640596610454, 17545493636135106882
```

We order them: 
```json
327830662700023863, 1544660713920769741, 3722572335198690747, 4035298408703112487, 5375153024761395986, 6692862674045639924, 7554992472722769382, 8495646299498670407, 9015192917032127462, 9371480197312631464, 11349000119560803050, 11617180555990659053, 14362607901913361150, 14400604751394908311, 16173382640596610454, 16283171823286969215, 16474393573432639799, 16852903019784931493, 16917897951851071986, 17545493636135106882
```

We build the solution string by concatenating those numbers together :
```json
32783066270002386315446607139207697413722572335198690747403529840870311248753751530247613959866692862674045639924755499247272276938284956462994986704079015192917032127462937148019731263146411349000119560803050116171805559906590531436260790191336115014400604751394908311161733826405966104541628317182328696921516474393573432639799168529030197849314931691789795185107198617545493636135106882
```

We hash the solution: `7d5fb906c70df5d43275e30bb044f64fbd5b4c2a2c8a92597700c7d1709a202b`. 

Not matching the `9098` prefix sent by the Central Authority server...

We keep trying with new random nonce.

Nonce: `37185758862`
Seed: `\x6a\x1b\xc5\x93\x3d\x93\xed\x33`
Solution String:
```json
```
**TODO: find valid nonce**

How lucky we are, another CSCoin awarded to our wallet. That's pretty much what mining is about. Generate a challenge dataset, solve it and check if the solution hash is valid. Rinse and repeat!

## Challenge Type

### Sorted List

<div class="challenge-section">**Challenge Name**: sorted_list
<div class="challenge-parameter-section">**Parameter(s)**
**nb_elements**: Number of Integer to sort in descending order
</div>
**Solution String formatting**

Append all integer into the right order in the solution string.
**Example**: 2, 3, 4, 5, 400 

                    Solution String = 2345400

</div>

#### Reverse Sorted List

<div class="challenge-section">**Challenge Name**: reverse_sorted_list
<div class="challenge-parameter-section">**Parameter(s)**
**nb_elements**: Number of Integer to sort in descending order
</div>
**Solution String formatting**

Append all integer into the right order in the solution string.
**Example**: 2, 3, 4, 5, 400 

                    Solution String = 4005432

</div>

More challenges will be added later...

### Wallet

A wallet is a RSA key pair of 1024 bits. To send or receive coins, we use the Wallet Id. The Wallet Id is a SHA256 Hash of your public key in DER ([Distinguished Encoding Rules](https://en.wikipedia.org/wiki/X.690#DER_encoding)) format.

				You need your private key to sign the submission message and create transaction message to prove that you're the owner of the wallet.

				You will need to register your public key on the Central Authority Server, to be able to do submission and create transaction.

                To calculate your Wallet balance, you need to retrieve all the transactions and compute your transactions.

### Message Signature

We are using RSA digital signature protocol according to PKCS#1 v1.5

				Some message required a signature, to validate that you're the owner of the wallet. 

				To generate a valid signature, in the command that need one. We specify the string value to hash with SHA256\. 

				Normally this is the arguments of the command, concatenated together separated with a comma (,).

				The message is always encoded in ASCII.

				You need to use the hash digest and sign it with your private key, to generate the signature.

				Your signature must be represented in hexadecimal in your command.

				The server will try to validate your signature against your public key

### Communication with the Central Authority

The Central Authority Server use the WebSocket protocol to communicate.

                The server URI is **wss://cscoins.2017.csgames.org:8989/client**

                All data sended and received are serialized into JSON. The server is waiting for a Command.

                The server is answering with a command response.

                If the field success is true, the command execution is successful, other fields can also be in the response, depending on the command executed.

#### Available commands

*   [get_current_challenge](#get-current-challenge-command)
*   [get_challenge_solution](#get-challenge-solution-command)
*   [close](#close-command)
*   [register_wallet](#register-wallet-command)
*   [get_transactions](#get-transactions-command)
*   [create_transaction](#create-transaction-command)
*   [submission](#submission-command)
*   [ca_server_info](#ca-server-info-command)

#### Command object

<table class="table .table-striped"><thead><tr><th>Field Name</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>command</td><td>String</td><td>The name of the command. Example: get_challenge_solution, create_transaction, register_wallet,...</td></tr><tr><td>args</td><td>Dictionary <String, Object></td><td>Parameters for the command, see each command documentation</td></tr></tbody></table>

#### Get Current Challenge

<div>

Fetch the current problem set from the Central Authority

**Command Name: **get_current_challenge

##### Argument(s)

There's no arguments.

##### Response

<table class="table .table-striped"><thead><tr><th>Field name</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>success</td><td>Boolean</td><td>-</td></tr><tr><td>time_left</td><td>Integer</td><td>Time left in seconds to solve the problem set.</td></tr><tr><td>challenge_id</td><td>Integer</td><td>Current Challenge Id</td></tr><tr><td>challenge_name</td><td>String</td><td>Current Challenge name</td></tr><tr><td>hash_prefix</td><td>String</td><td>Solution hash prefix</td></tr><tr><td>parameters</td><td>Dictionary<String, Object></td><td>Parameters of the challenge, they can changed depending on the challenge name</td></tr></tbody></table></div>

#### Get previous solutions

<div>

Fetch the solution of a challenge

**Command Name: **get_challenge_solution

##### Argument(s)

<table class="table .table-striped"><thead><tr><th>Name</th><th>Type</th><th>Value</th></tr></thead><tbody><tr><td>challenge_id</td><td>Integer</td><td>Challenge Id of the solution wanted</td></tr></tbody></table>

##### Response

<table class="table .table-striped"><thead><tr><th>Field name</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>success</td><td>Boolean</td><td>-</td></tr><tr><td>challenge_id</td><td>Integer</td><td>Challenge Id of the solution</td></tr><tr><td>challenge_name</td><td>String</td><td>Challenge name</td></tr><tr><td>nonce</td><td>Integer</td><td>Solution Nonce of the Challenge</td></tr><tr><td>hash</td><td>Integer</td><td>Solution Hash of the Challenge</td></tr><tr><td>solution_string</td><td>String</td><td>Solution String of the Challenge</td></tr><tr><td>parameters</td><td>Dictionary<String, Object></td><td>Parameters of the challenge</td></tr></tbody></table></div>

#### Close connection

<div>

Close the connection with the Central Authority Server

**Command Name: **close

##### Argument(s)

There's no arguments.

##### Response

There's no response.

</div>

#### Register a new Wallet

<div>

Register your Wallet PublicKey with the Central Authority.

**Command Name: **register_wallet

##### Argument(s)

<table class="table .table-striped"><thead></thead><tbody><tr><th>Name</th><th>Type</th><th>Value</th></tr></tbody><tbody><tr><td>name</td><td>String</td><td>Your Wallet Name, you should use your Team Name here</td></tr><tr><td>key</td><td>String</td><td>Your wallet public key, in PEM Format ([Privacy-enhanced Electronic Mail](https://en.wikipedia.org/wiki/Privacy-enhanced_Electronic_Mail)).</td></tr><tr><td>signature</td><td>String</td><td>[Message Signature](#message-signature) in hexadecimal format. The message used is `wallet_id`, not hashed, because it's already an hash of your public key.</td></tr></tbody></table>

##### Response

<table class="table .table-striped"><thead><tr><th>Field name</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>success</td><td>Boolean</td><td>-</td></tr><tr><td>wallet_id</td><td>String</td><td>Your new Wallet Id</td></tr></tbody></table></div>

#### Get Transactions

<div>

Get transactions history from the Central Authority.

**Command Name: **get_transactions

##### Argument(s)

<table class="table .table-striped"><thead><tr><th>Name</th><th>Type</th><th>Value</th></tr></thead><tbody><tr><td>start</td><td>Integer</td><td>Starting index</td></tr><tr><td>count</td><td>Integer</td><td>Number of transactions to fetch. Maximum 100.</td></tr></tbody></table>

##### Response

<table class="table .table-striped"><thead><tr><th>Field name</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>success</td><td>Boolean</td><td>-</td></tr><tr><td>count</td><td>Integer</td><td>Number of transactions</td></tr><tr><td>transactions</td><td>Array<Transaction></td><td>Transaction(s)</td></tr></tbody></table>

##### Transaction Object

<table class="table .table-striped"><thead><tr><th>Field Name</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>id</td><td>Integer</td><td>Transaction Id</td></tr><tr><td>source</td><td>String</td><td>Source Address (Wallet Id or alias)</td></tr><tr><td>recipient</td><td>String</td><td>Recipient Address (Wallet Id or alias)</td></tr><tr><td>amount</td><td>Decimal</td><td>Transaction Amount</td></tr></tbody></table></div>

#### Create a new Transaction (Send coins)

<div>

Create a new Transaction. Sending coins to another wallet

**Command Name: **create_transaction

##### Argument(s)

<table class="table .table-striped"><thead><tr><th>Name</th><th>Type</th><th>Value</th></tr></thead><tbody><tr><td>source</td><td>String</td><td>Your Wallet Id</td></tr><tr><td>recipient</td><td>String</td><td>Recipient Wallet Id</td></tr><tr><td>amount</td><td>Decimal</td><td>Amount to send, Minimum 0.00001.</td></tr><tr><td>signature</td><td>String</td><td>[Message Signature](#message-signature) in hexadecimal format. The message used is `source,recipient,amount`. The amount is a decimal number formatted with 5 digit of precision.
**Example:** Amount = 2, would be writted as 2.00000 in the message.</td></tr></tbody></table>

##### Response

<table class="table .table-striped"><thead><tr><th>Field name</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>success</td><td>Boolean</td><td>-</td></tr><tr><td>id</td><td>Integer</td><td>New Transaction Id</td></tr></tbody></table></div>

#### Submit a problem solution

<div>

Submit a solution for a challenge, it must be the current challenge, else it will be ignored.

**Command Name: **submission

##### Argument(s)

<table class="table .table-striped"><thead><tr><th>Name</th><th>Type</th><th>Value</th></tr></thead><tbody><tr><td>wallet_id</td><td>String</td><td>Challenge Id</td></tr><tr><td>challenge_id</td><td>Integer</td><td>Challenge Id</td></tr><tr><td>nonce</td><td>Integer</td><td>Solution nonce</td></tr><tr><td>hash</td><td>String</td><td>Solution Hash in hexadecimal format.</td></tr><tr><td>signature</td><td>String</td><td>[Message Signature](#message-signature) in hexadecimal format. The message used is `challenge_id,nonce,hash`</td></tr></tbody></table>

##### Response

<table class="table .table-striped"><thead><tr><th>Field name</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>success</td><td>Boolean</td><td>-</td></tr><tr><td>submission_id</td><td>Integer</td><td>Your submission Id for this challenge</td></tr></tbody></table></div>

#### Get Central Authority Server Information

<div>

Fetch the current information of the Central Authority Server

**Command Name: **ca_server_info

##### Argument(s)

There's no arguments.

##### Response

<table class="table .table-striped"><thead><tr><th>Field name</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>success</td><td>Boolean</td><td>-</td></tr><tr><td>minutes_per_challenge</td><td>Integer</td><td>Maximum length of a challenge in minutes.</td></tr><tr><td>coins_per_challenge</td><td>Integer</td><td>Coins awarded for a subsmission.</td></tr><tr><td>min_transaction_amount</td><td>Decimal</td><td>Minimum transaction amount.</td></tr><tr><td>ca_public_key</td><td>String</td><td>Central Authority PublicKey in PEM Format ([Privacy-enhanced Electronic Mail](https://en.wikipedia.org/wiki/Privacy-enhanced_Electronic_Mail)).</td></tr></tbody></table></div></div>
    