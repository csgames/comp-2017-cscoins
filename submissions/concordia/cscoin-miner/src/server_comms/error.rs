
//! # CS Coin Client Error
//!
//! Module containing that various errors that can be
//! encountered whiel using the CSCoinClient
//!
//! Reference: https://github.com/csgames/cscoins#communication-with-the-central-authority

use std::io::Error as IOError;
use std::string::FromUtf8Error;

use openssl::ssl::error::SslError;
use serde_json::error::Error as JSONError;
use websocket::result::WebSocketError;

#[derive(Debug)]
pub enum CSCoinClientError {
    IOErr(IOError),
    JSONErr(JSONError),
    SSLErr(SslError),
    WebSockErr(WebSocketError),
    UTF8Err(FromUtf8Error)
}
