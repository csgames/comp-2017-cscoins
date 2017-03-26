
//! # Server Comms
//!
//! Modules to communicate with the server, includes
//! server commands and response structs.
//!
//! Reference: https://github.com/csgames/cscoins#communication-with-the-central-authority

use std::fs;
use std::fs::File;
use std::io::{Cursor, Read, Write};
use std::mem;
use std::process::Command;

use crypto::digest::Digest;
use crypto::sha2::Sha256;
use openssl::crypto::pkey::{EncryptionPadding, PKey};
use openssl::ssl::{SslContext, SslMethod};
use rustc_serialize::hex::ToHex;
use serde;
use serde_json;
use serde_json::map::Map;
use serde_json::Value;
use serde_json::Number;
//NOTE: Some imports are renamed with a WSC prefix because
//      yes... there are different implementations of the
//      same type and yes we are using both... The WSC
//      prefixed ones are the types used to declare the
//      WebSockClient type args.
use websocket::{Client as WebSockClient, Message, Receiver, Sender};
use websocket::client::request::Url;
use websocket::dataframe::DataFrame as WSCDataFrame; //See note above
use websocket::receiver::Receiver as WSCReceiver; //See note above
use websocket::sender::Sender as WSCSender; //See note above
use websocket::stream::WebSocketStream;
use websocket::ws::dataframe::DataFrame;

use server_comms::error::CSCoinClientError;
use server_comms::cmd_response::{CurrentChallenge,
                                 ChallengeSolution,
                                 RegisterWallet,
                                 Transactions,
                                 CreateTransaction,
                                 SubmitProblem,
                                 CAServerInfo};

pub mod cmd_response;
pub mod error;


//---------------------------------------------------------
// Consts
//---------------------------------------------------------

pub static DEFAULT_URI:   &'static str = "wss://cscoins.2017.csgames.org:8989/client";
pub static TEST_URI:      &'static str = "ws://127.0.0.1:8989/client";
pub static PRIV_PEM_FILE: &'static str = "private_key.pem";
pub static PUB_PEM_FILE:  &'static str = "public_key.pem";

//---------------------------------------------------------
// Payload Struct
//---------------------------------------------------------

#[derive(Serialize)]
pub struct CommandPayload {
    pub command: String,
    pub args:    Option<Map<String, Value>>
}


//---------------------------------------------------------
// Client
//---------------------------------------------------------
//Holds the client state

pub struct CSCoinClient {
    client:    WebSockClient<WSCDataFrame, WSCSender<WebSocketStream>, WSCReceiver<WebSocketStream>>,
    keys:      PKey,
    wallet_id: String
}

impl CSCoinClient {

    //Use this to connect to the CA Server
    pub fn connect(server_uri: &'static str) -> Result<CSCoinClient, CSCoinClientError> {

        //Load keys
        CSCoinClient::create_rsa_keys();
        let pkey = CSCoinClient::load_rsa_keys();

        // safe to unwrap, if this crashes then we have a
        // typo in our constant.
        let url      = Url::parse(server_uri).unwrap();      // Parse url
        let request  = try!(WebSockClient::connect(url)      // Connect to server
            .map_err(CSCoinClientError::WebSockErr));
        let response = try!(request.send()                   // Send request
            .map_err(CSCoinClientError::WebSockErr));
        try!(response.validate()                             // Validate response
            .map_err(CSCoinClientError::WebSockErr));

        //Computer wallet id
        let mut hasher = Sha256::new();
        hasher.input(&pkey.save_pub());

        println!("Connected to server with wallet ID: {}", hasher.result_str());

        let mut ret_val = CSCoinClient {
            client:    response.begin(),
            keys:      pkey,
            wallet_id: hasher.result_str()
        };

        ret_val.register_wallet("ConcordiaUniversity").unwrap();

        Ok(ret_val)

    }

    //Implementation of close command
    //Reference: https://github.com/csgames/cscoins#close-connection
    pub fn disconnect(&mut self) -> Result<(), CSCoinClientError> {

        //JSONify payload
        let payload = try!(serde_json::to_string(&CommandPayload{
            command: "close".to_string(),
            args:    Option::None
        }).map_err(CSCoinClientError::JSONErr));

        //Send Payload
        try!(self.client.send_message(&Message::text(payload))
            .map_err(CSCoinClientError::WebSockErr));

        //Close client side connection
        try!(self.client.shutdown().map_err(CSCoinClientError::IOErr));

        drop(self);
        return Ok(())
    }

    //Helper command
    pub fn send_command<D: serde::Deserialize>(&mut self, command_payload: CommandPayload) -> Result<D, CSCoinClientError> {

        //JSONify payload
        let payload = try!(serde_json::to_string(&command_payload)
            .map_err(CSCoinClientError::JSONErr));

        println!("Sending command: {}", command_payload.command);

        //Send Payload
        try!(self.client.send_message(&Message::text(payload))
            .map_err(CSCoinClientError::WebSockErr));

        let mut receiver = self.client.get_mut_receiver();

        //Receive and extract response
        let response: Message = try!(receiver.recv_message() //get response
            .map_err(CSCoinClientError::WebSockErr));
        let mut response_cursor = Cursor::new(Vec::new());   //create essentially what is a buffer
        try!(response.write_payload(&mut response_cursor)    //write payload to buffer
            .map_err(CSCoinClientError::WebSockErr));
        //Turn buffer data to String
        let response_str = try!(String::from_utf8(response_cursor.into_inner())
            .map_err(CSCoinClientError::UTF8Err));

        serde_json::from_str(&response_str[..]).map_err(CSCoinClientError::JSONErr)
    }


    //Utils

    pub fn create_rsa_keys() {

        //TODO: Error checking

        let mut pkey = PKey::new();
        pkey.gen(1024);

        //Write private key if non existant
        let priv_meta = fs::metadata(PRIV_PEM_FILE);
        if priv_meta.is_err() || !priv_meta.unwrap().is_file() {
            let mut priv_file = File::create(PRIV_PEM_FILE).unwrap();
            pkey.write_pem(&mut priv_file).unwrap();
        }

        //Write public key if non existant
        let pub_meta = fs::metadata(PUB_PEM_FILE);
        if pub_meta.is_err() || !pub_meta.unwrap().is_file() {
            let mut pub_file = File::create(PUB_PEM_FILE).unwrap();
            pkey.write_pub_pem(&mut pub_file).unwrap();
        }

    }

    pub fn load_rsa_keys() -> PKey {

        //TODO: Error checking
        let mut priv_file = File::open(PRIV_PEM_FILE).unwrap();
        let mut pkey      = PKey::private_rsa_key_from_pem(&mut priv_file).unwrap();
        pkey
    }

    pub fn compute_signature(&mut self, data: &[u8]) -> String {

        let mut hasher:      Sha256   = Sha256::new();
        let mut hash_result: [u8; 32] = [0; 32];

        hasher.input(&data);
        hasher.result(&mut hash_result);

        let signature_bytes = self.keys.sign(&hash_result);
        signature_bytes.as_slice().to_hex()
    }

    /// ## Get Current Challenge
    ///
    /// Fetch the current problem set from the Central Authority
    ///
    /// Arguments: none
    /// Response:  CurrentChallenge
    ///
    /// References: https://github.com/csgames/cscoins#get-current-challenge
    pub fn get_current_challenge(&mut self) -> Result<CurrentChallenge, CSCoinClientError> {
        self.send_command(CommandPayload{
            command: "get_current_challenge".to_string(),
            args:    Option::None
        })
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
    pub fn get_challenge_solution(&mut self, challenge_id: u64) -> Result<ChallengeSolution, CSCoinClientError> {
        let mut args: Map<String, Value> = Map::new();
        args.insert("challenge_id".to_string(), Value::Number(Number::from(challenge_id)));
        self.send_command(CommandPayload{
            command: "get_challenge_solution".to_string(),
            args:    Some(args)
        })
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
    pub fn register_wallet(&mut self, name: &'static str) -> Result<RegisterWallet, CSCoinClientError> {

        //TODO: ERROR CHECKING
        //TODO: SAVE WALLET ID

        //Get key in PEM format
        let mut key_cursor = Cursor::new(Vec::new());
        self.keys.write_pub_pem(&mut key_cursor).unwrap();
        let key = String::from_utf8(key_cursor.into_inner()).unwrap();

        //Get signature
        let pub_key_der = self.keys.save_pub();
        let signature = self.compute_signature(&pub_key_der);

        let mut args: Map<String, Value> = Map::new();
        args.insert("name".to_string(),      Value::String(name.to_string()));
        args.insert("key".to_string(),       Value::String(key));
        args.insert("signature".to_string(), Value::String(signature));
        self.send_command(CommandPayload {
            command: "register_wallet".to_string(),
            args:    Some(args)
        })
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
    pub fn get_transactions(&mut self, start: u64, count: u64) -> Result<Transactions, CSCoinClientError> {
        let mut args: Map<String, Value> = Map::new();
        args.insert("start".to_string(), Value::Number(Number::from(start)));
        args.insert("count".to_string(), Value::Number(Number::from(count)));
        self.send_command(CommandPayload{
            command: "get_transactions".to_string(),
            args:    Some(args)
        })
    }


    //TODO: f64 error check (Rust has but JSON doesnt have NaN nor Infinity
    // serde_json checks for that)
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
    pub fn create_transaction(&mut self, recipient: String, amount: f64) -> Result<CreateTransaction, CSCoinClientError> {

        let signature_data = format!("{},{},{:.5}", self.wallet_id.clone(), recipient, amount);
        let signature      = self.compute_signature(signature_data.as_bytes());

        let mut args: Map<String, Value> = Map::new();
        args.insert("source".to_string(),    Value::String(self.wallet_id.clone()));
        args.insert("recipient".to_string(), Value::String(recipient));
        args.insert("amount".to_string(),    Value::Number(Number::from_f64(amount).unwrap()));
        args.insert("signature".to_string(), Value::String(signature));
        self.send_command(CommandPayload{
            command: "create_transaction".to_string(),
            args:    Some(args)
        })
    }


    /// ## Submit a problem solution
    ///
    /// Submit a solution for the current challenge, awarding CSCoins to the miner if the solution is valid.
    ///
    /// Command:   "submission"
    /// Arguments: wallet_id: String
    ///            nonce:     String
    ///            hash:      String
    /// Response:  SubmitProblem
    ///
    /// References: https://github.com/csgames/cscoins#submit-a-problem-solution
    pub fn submission(&mut self, nonce: String) -> Result<SubmitProblem, CSCoinClientError> {
        let mut args: Map<String, Value> = Map::new();
        args.insert("nonce".to_string(),        Value::String(nonce));
        args.insert("wallet_id".to_string(),    Value::String(self.wallet_id.clone()));
        self.send_command(CommandPayload{
            command: "submission".to_string(),
            args:    Some(args)
        })
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
    pub fn ca_server_info(&mut self) -> Result<CAServerInfo, CSCoinClientError> {
        self.send_command(CommandPayload{
            command: "ca_server_info".to_string(),
            args:    Option::None
        })
    }

}


#[test]
fn create_rsa_keys() {
    CSCoinClient::create_rsa_keys();
}

#[test]
fn load_rsa_keys() {
    CSCoinClient::load_rsa_keys();
}

#[test]
fn test_connect_disconnect() {
    let mut client = match CSCoinClient::connect(TEST_URI){
        Ok(client) => client,
        Err(err)   => panic!("Error on connect: {:?}", err)
    };
    match client.disconnect() {
        Ok(())   => (),
        Err(err) => panic!("Error on disconnect: {:?}", err)
    }
}

#[test]
fn test_get_current_challenge() {

    let mut client = match CSCoinClient::connect(TEST_URI){
        Ok(client) => client,
        Err(err)   => panic!("Error on connect: {:?}", err)
    };

    let challenge: CurrentChallenge = match client.get_current_challenge() {
        Ok(challenge) => challenge,
        Err(err)      => panic!("Error on get_current_challenge(): {:?}", err)
    };

    match client.disconnect() {
        Ok(())   => (),
        Err(err) => panic!("Error on disconnect: {:?}", err)
    }

}

#[test]
fn test_get_challenge_solution() {

    let mut client = match CSCoinClient::connect(TEST_URI){
        Ok(client) => client,
        Err(err)   => panic!("Error on connect: {:?}", err)
    };

    let solution: ChallengeSolution = match client.get_challenge_solution(1) {
        Ok(solution) => solution,
        Err(err)     => panic!("Error on get_challenge_solution(1): {:?}", err)
    };

    match client.disconnect() {
        Ok(())   => (),
        Err(err) => panic!("Error on disconnect: {:?}", err)
    }

}

#[test]
fn test_register_wallet() {

    let mut client = match CSCoinClient::connect(TEST_URI){
        Ok(client) => client,
        Err(err)   => panic!("Error on connect: {:?}", err)
    };

    let wallet: RegisterWallet = match client.register_wallet("Concordia University") {
        Ok(wallet) => wallet,
        Err(err)   => panic!("Error on register_wallet(\"Concordia University\"): {:?}", err)
    };

    match client.disconnect() {
        Ok(())   => (),
        Err(err) => panic!("Error on disconnect: {:?}", err)
    }

}

#[test]
fn test_get_transactions() {

    let mut client = match CSCoinClient::connect(TEST_URI){
        Ok(client) => client,
        Err(err)   => panic!("Error on connect: {:?}", err)
    };

    let wallet: Transactions = match client.get_transactions(0, 100) {
        Ok(wallet) => wallet,
        Err(err)   => panic!("Error on get_transactions(0, 100): {:?}", err)
    };

    match client.disconnect() {
        Ok(())   => (),
        Err(err) => panic!("Error on disconnect: {:?}", err)
    }

}

#[test]
fn test_create_transaction() {
    //TODO: once we get other clients and some coins/submissions
}

#[test]
fn test_submission() {
    //TODO: once we get other clients and some coins/submissions
}

#[test]
fn test_ca_server_info() {

    let mut client = match CSCoinClient::connect(TEST_URI){
        Ok(client) => client,
        Err(err)   => panic!("Error on connect: {:?}", err)
    };

    let challenge: CAServerInfo = match client.ca_server_info() {
        Ok(challenge) => challenge,
        Err(err)      => panic!("Error on ca_server_info(): {:?}", err)
    };

    match client.disconnect() {
        Ok(())   => (),
        Err(err) => panic!("Error on disconnect: {:?}", err)
    }

}
