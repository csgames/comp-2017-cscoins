
pub mod shortest_path;

use mersenne_twister::MersenneTwister;
use rand::{Rng, SeedableRng, thread_rng, ThreadRng};
use std::mem;
use std::marker::Copy;
use std::u32;
use std::cmp::Ordering;
use std::cmp;
use crypto::digest::Digest;
use crypto::sha2::Sha256;
use byteorder::{ByteOrder, LittleEndian};
use rustc_serialize::hex::ToHex;
use std::collections::BinaryHeap;
use fnv::FnvHashSet;
use fnv::FnvHashMap;
use itertools::Itertools;
use client_miner::shortest_path::{Grid, a_star, reconstruct_path};

pub struct Miner{
    rng: MersenneTwister,
    lastSeed: u64,
    hasher: Sha256,
    nonce_rng: ThreadRng
}

impl Miner{

    pub fn new() -> Miner
    {
        Miner{
            rng: SeedableRng::from_seed(0),
            lastSeed: 0,
            hasher: Sha256::new(),
            nonce_rng: thread_rng()
        }
    }

    pub fn sort_list<'a>(&'a mut self, num_ints: usize) -> String
    {
        let mut output=BinaryHeap::with_capacity(num_ints);

        for x in 0..num_ints {
            output.push(self.rng.next_u64());
        }

        let mut numbers = output.into_sorted_vec();

        return numbers.iter().join("")
    }


    pub fn reverse_sort_list<'a>(&'a mut self, num_ints: usize) -> String
    {
        let mut output=BinaryHeap::with_capacity(num_ints);

        for x in 0..num_ints {
            output.push(self.rng.next_u64());
        }

        let mut numbers = output.into_sorted_vec();

        numbers.reverse();

        return numbers.iter().join("")

    }

    //Passes the concatenation of the last_solution hash and the nonce, and plugs the result into a u64
    pub fn get_seed(&mut self, last_solution:&String, nonce:u64) -> u64
    {
        let mut new_seed:[u8;32]=[0;32];

        self.hasher.reset();

        self.hasher.input_str(&(format!("{}{}", last_solution, nonce.to_string())));

        self.hasher.result(&mut new_seed);

        let seed: u64 = LittleEndian::read_u64(&new_seed[0..8]);

        return seed;

    }

    //Solves the sorted list challenge, and returns a tuple (hash, nonce)
    pub fn sorted_list_challenge(&mut self, last_solution:&String, prefix:&String, num_ints:u64) -> (String,u64)
    {

        let nonce = self.nonce_rng.next_u64();

        let seed = self.get_seed(last_solution, nonce);

        self.rng.reseed(seed);

        let mut concat_string:String = self.sort_list(num_ints as usize);

        self.hasher.reset();

        self.hasher.input_str(&concat_string);

	let mut hash_buf:[u8;32]=[0;32];

        self.hasher.result(&mut hash_buf);

	let hash_res = (&hash_buf).to_hex();

        return (hash_res, nonce);

    }

    pub fn reverse_challenge(&mut self, last_solution:&String, prefix: &String, num_ints:u64) ->(String,u64)
    {

        let nonce = self.nonce_rng.next_u64();

        let seed = self.get_seed(last_solution, nonce);

        self.rng.reseed(seed);

        let mut concat_string:String = self.reverse_sort_list(num_ints as usize);

        self.hasher.reset();

        self.hasher.input_str(&concat_string);
        
        let mut hash_buf:[u8;32]=[0;32];

        self.hasher.result(&mut hash_buf);

	let hash_res = (&hash_buf).to_hex();

        return (hash_res, nonce);

    }




    pub fn shortest_path_challenge(&mut self, last_solution:&String, prefix: &String, size:u64, num_blockers: u64, num_loops: u64) -> Option<(String,u64)>
    {
        for i in 0..num_loops{

            let nonce = self.nonce_rng.next_u64();

            let seed=self.get_seed(last_solution, nonce);

            self.rng.reseed(seed);

            let mut new_grid = Grid::new(size as usize, num_blockers);

            new_grid.populate(&mut self.rng);

            if let Some(solution) = a_star(&new_grid){
                let (came_from, cost) = solution;
                let solution_string:String = reconstruct_path(&new_grid, came_from, cost);

                self.hasher.reset();

                self.hasher.input_str(&solution_string);

                let hash_res=self.hasher.result_str();

                return Some((hash_res,nonce));
            }
        }

        None

    }
}

//To be replaced by thread dispatcher



// fn solve_challenge(current_challenge: CurrentChallenge)->Option<(String, u64)>{
//
//     let mut miner = Miner::new();
//
//     let id = current_challenge.challenge_id;
//
//     match current_challenge.parameters{
//         CurrentChallengeParams {grid_size: Some(x), nb_blockers: num @ Some(_), .. }=>{
//             return miner.solve_shortest_path(current_challenge.last_solution_hash, sz.unwrap() as usize, num.unwrap());
//         },
//         CurrentChallengeParams {grid_size: None, nb_blockers: None, nb_elements: num_int  @ Some(_)}=>{
//             let reverse = current_challenge.challenge_name=="reverse_sorted_list".to_string();
//             if reverse {return miner.reverse_challenge(current_challenge.last_solution_hash, num_int.unwrap());}
//             else {
//                 return miner.sorted_list_challenge(current_challenge.last_solution_hash, num_int.unwrap());
//             }
//         },
//         _=>None
//     }
// }
