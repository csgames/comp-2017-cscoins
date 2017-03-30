
//TODO: Tests
//TODO: Don't forget the Close Conection command
//      (no args, no response)
//      Reference: https://github.com/csgames/cscoins#close-connection


//! # Command Response
//!
//! Module containing the command response structures
//! interpreted from JSON while communicating with the
//! server
//!
//! Reference: https://github.com/csgames/cscoins#available-commands


use serde_json::Map;
use serde_json::Value;


/// ## Command object
///
/// Generic struct for sending commands.
///
/// References: https://github.com/csgames/cscoins#command-object
///             https://docs.serde.rs/serde_json/struct.Map.html
///             https://docs.serde.rs/serde_json/value/enum.Value.html

#[derive(Serialize, Debug)]
pub struct CommandObject {
    pub command: String,
    pub args:    Map<String, Value>,
}


/// ## Get Current Challenge
///
/// Fetch the current problem set from the Central Authority
///
/// Arguments: none
/// Response:  CurrentChallenge
///
/// References: https://github.com/csgames/cscoins#get-current-challenge

#[derive(Deserialize, Debug)]
pub struct CurrentChallenge {
    pub time_left:          u64,
    pub challenge_id:       u64,
    pub challenge_name:     String,
    pub hash_prefix:        String,
    pub last_solution_hash: String,
    pub parameters:         CurrentChallengeParams
}

//Sub-component of the CurrentChallenge struct
#[derive(Deserialize, Debug)]
pub struct CurrentChallengeParams {
    pub grid_size:   Option<u64>,
    pub nb_blockers: Option<u64>,
    pub nb_elements: Option<u64>
}


/// ## Get Challenge Solution
///
/// Fetch the solution of a challenge
///
/// Command:   "get_challenge_solution"
/// Arguments: challenge_id: u64
/// Response:  ChallengeSolution
///
/// References: https://github.com/csgames/cscoins#get-current-challenge

#[derive(Deserialize, Debug)]
pub struct ChallengeSolution {
    pub challenge_id:   u64,
    pub challenge_name: String,
    pub nonce:          u64,
    pub hash:           String
}


/// ## Register a New Wallet
///
/// Register your Wallet's public key with the Central Authority.
///
/// Command:   "register_wallet"
/// Arguments: name:      String
///            key:       String
///            signature: String
/// Response:  RegisterWallet
///
/// References: https://github.com/csgames/cscoins#register-a-new-wallet

#[derive(Deserialize, Debug)]
pub struct RegisterWallet {
    pub error: Option<String>    //Unclear if empty/missing when no error?
}


/// ## Get Transactions
///
/// Get transactions history from the Central Authority.
///
/// Command:   "get_transactions"
/// Arguments: start: u64
///            count: u64
/// Response:  Transactions
///
/// References: https://github.com/csgames/cscoins#get-transactions

#[derive(Deserialize, Debug)]
pub struct Transactions {
    pub error:        Option<String>,  //Unclear if empty/missing when no error?
    pub transactions: Vec<Transaction>
}

//Element of the transactions array
#[derive(Deserialize, Debug)]
pub struct Transaction {
    pub id:        u64,
    pub source:    String,
    pub recipient: String,
    pub amount:    f64
}


/// ## Create a new Transaction (Send coins)
///
/// Create a new Transaction, sending coins to another wallet
///
/// Command:   "create_transaction"
/// Arguments: source:    String
///            recipient: String
///            amount:    f64
///            signature: String
/// Response:  CreateTransaction
///
/// References: https://github.com/csgames/cscoins#create-a-new-transaction-send-coins

#[derive(Deserialize, Debug)]
pub struct CreateTransaction {
    pub error: Option<String>,  //Unclear if empty/missing when no error?
    pub id:    u64
}


/// ## Submit a problem solution
///
/// Submit a solution for the current challenge, awarding CSCoins to the miner if the solution is valid.
///
/// Command:   "submission"
/// Arguments: wallet_id: String
///            nonce:     String
/// Response:  SubmitProblem
///
/// References: https://github.com/csgames/cscoins#submit-a-problem-solution

#[derive(Deserialize, Debug)]
pub struct SubmitProblem {
    #[serde(rename = "type")]
    pub challenge_type: String,
    pub error:          Option<String>,  //Unclear if empty/missing when no error?
}


/// ## Get Central Authority Server Information
///
/// Fetch the current information of the Central Authority server
///
/// Command:   "ca_server_info"
/// Arguments: none
/// Response:  CAServerInfo
///
/// References: https://github.com/csgames/cscoins#get-central-authority-server-information

#[derive(Deserialize, Debug)]
pub struct CAServerInfo {
    minutes_per_challenge:  f64,
    coins_per_challenge:    f64,
    min_transaction_amount: f64,
    ca_public_key:          String
}
