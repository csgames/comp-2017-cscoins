extern crate mersenne_twister;
extern crate crypto;
extern crate rand;
extern crate byteorder;
extern crate itertools;
extern crate openssl;
extern crate rustc_serialize;
extern crate serde;
extern crate fnv;
#[macro_use]
extern crate serde_derive;
#[macro_use]
extern crate serde_json;
extern crate websocket;

extern crate ctrlc;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::time::Instant;

//Everything to do with communicating with the server.
mod server_comms;
mod client_miner;
mod threads;


//-----------------------------------------------------------------------------
// Consts
//-----------------------------------------------------------------------------

//Number of threads to use
static NUM_THREADS:     u64 = 8;
//Number of hashes to make per processing chunk
//static WORK_CHUNK_SIZE: u64 = 100;                GO SEE WORKER FILE


fn main() {

    let is_running = Arc::new(AtomicBool::new(true));
    let r = is_running.clone();
    ctrlc::set_handler(move || {
        r.store(false, Ordering::SeqCst);
    }).expect("Error setting Ctrl-C handler");

    //Init comms
    let mut client               = server_comms::CSCoinClient::connect(server_comms::DEFAULT_URI).unwrap();
    let mut worker_manager       = threads::ThreadManager::new(NUM_THREADS);
    let mut challenge_begin_time = Instant::now();
    let mut challenge_time_left;


    //get first challenge and assign to workers
    let first_challenge  = client.get_current_challenge().unwrap();
    challenge_time_left = first_challenge.time_left;
    println!("First challenge: {:?}", first_challenge);

    let first_assignment = get_assignment(first_challenge);
    println!("First assignment: {:?}", first_assignment);

    worker_manager.setup(first_assignment.clone());

    println!("Thread #1/{} started. (Main thread)", NUM_THREADS);
    while is_running.load(Ordering::SeqCst) {

        //check if connection dropped

        //do some work in main thread
        worker_manager.do_main_work();

        //check if a worker found a solution
        match worker_manager.get_solution() {
            Some(nonce) => {

                //Submit
                println!("Submission result: {:?}", client.submission(nonce)); //TODO: ERROR CHECKING

                /*//get new challenge
                let new_challenge   = client.get_current_challenge().unwrap(); //TODO: ERROR CHECK
                println!("New challenge after submission: {:?}", new_challenge);
                challenge_time_left = new_challenge.time_left;
                let new_assignment  = get_assignment(new_challenge);

                //Dispatch new assignment
                worker_manager.set_new_assignment(new_assignment);*/

                //get new challenge
                match client.get_current_challenge() {
                    Ok(new_challenge) => {
                        println!("New challenge after submission: {:?}", new_challenge);
                        challenge_time_left  = new_challenge.time_left;
                        challenge_begin_time = Instant::now();
                        let new_assignment   = get_assignment(new_challenge);

                        //Dispatch new assignment
                        worker_manager.set_new_assignment(new_assignment);
                    },
                    Err(err) => {
                        println!("Error getting new challenge after timeout: {:?}", err);
                    }
                };
            },
            None => {}
        }

        //Check if were out of time and need a new challenge
        if challenge_begin_time.elapsed().as_secs() >= challenge_time_left {

            println!("Challenge timed out... Trying for the next one...");

            //get new challenge
            match client.get_current_challenge() {
                Ok(new_challenge) => {
                    println!("New challenge after timeout: {:?}", new_challenge);
                    challenge_time_left  = new_challenge.time_left;
                    challenge_begin_time = Instant::now();
                    let new_assignment   = get_assignment(new_challenge);

                    //Dispatch new assignment
                    worker_manager.set_new_assignment(new_assignment);
                },
                Err(err) => {
                    println!("Error getting new challenge after timeout: {:?}", err);
                    println!("Going to try again...");
                }
            };
        }
        //if solution not found continue working
    }

    println!("\nStopping...");
    worker_manager.stop();
    client.disconnect().unwrap();

}


pub fn get_assignment(current_challenge: server_comms::cmd_response::CurrentChallenge) -> threads::ThreadAssignment {

    match &current_challenge.challenge_name[..] {
        "sorted_list" => {
            threads::ThreadAssignment::SortedList(
                current_challenge.last_solution_hash,
                current_challenge.hash_prefix,
                current_challenge.parameters.nb_elements.unwrap(),
                current_challenge.challenge_id
            )
        },
        "reverse_sorted_list" => {
            threads::ThreadAssignment::ReverseSortedList(
                current_challenge.last_solution_hash,
                current_challenge.hash_prefix,
                current_challenge.parameters.nb_elements.unwrap(),
                current_challenge.challenge_id
            )
        },
        "shortest_path" => {
            threads::ThreadAssignment::ShortestPath(
                current_challenge.last_solution_hash,
                current_challenge.hash_prefix,
                current_challenge.parameters.grid_size.unwrap(),
                current_challenge.parameters.nb_blockers.unwrap(),
                current_challenge.challenge_id
            )
        }
        _ => {
            panic!("Got an invalid challenge?????");
        }
    }

}
