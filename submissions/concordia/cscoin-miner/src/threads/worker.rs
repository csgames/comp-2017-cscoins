
use std::sync::Arc;
use std::sync::Mutex;
use std::sync::mpsc::Sender;
use std::sync::mpsc::Receiver;

use threads::ThreadAssignment;
use client_miner::Miner;

//Number of hashes to make per processing chunk
const WORK_CHUNK_SIZE: usize = 100;



pub struct Worker {
    current_assignment:  Arc<Mutex<ThreadAssignment>>,
    nonce_sender:        Arc<Mutex<Sender<String>>>,
    work_miner:          Miner
}

impl Worker {

    pub fn new(nonce_sender: Arc<Mutex<Sender<String>>>, assignment:   Arc<Mutex<ThreadAssignment>>) -> Worker {
        Worker{
            current_assignment:  assignment,
            nonce_sender:        nonce_sender,
            work_miner:          Miner::new()
        }
    }

    //True for workers, false for main (main does some extra stuff)
    pub fn do_work(&mut self, do_loop: bool) -> (){
        let mut found = false;
        let mut current_id: u64 = 0;
        while do_loop {

            let assignment_arc = self.current_assignment.clone();
            let assignment;

            { //Lock is scope based, lock for as little time as possible
                assignment = (*assignment_arc.lock().unwrap()).clone();
            }

            if found{
                  match assignment{
                  ThreadAssignment::SortedList(_, _, _, challenge_id)=>{
                    if challenge_id!=current_id{
                      found=false;
                      current_id=challenge_id;
                    }

                  },
                  ThreadAssignment::ReverseSortedList(_, _, _, challenge_id)=>{
                    if challenge_id!=current_id{
                      found=false;
                      current_id=challenge_id;
                    }

                  },
                  ThreadAssignment::ShortestPath(_, _, _, _, challenge_id)=>{
                    if challenge_id!=current_id{
                      found=false;
                      current_id=challenge_id;
                    }

                  },
                  _=>{found = false;}
                }
            }
            if !found{
            match assignment {
                ThreadAssignment::Stop => {break;},
                ThreadAssignment::SortedList(last_hash, prefix, num_int, challenge_id)=>{
                    let mut results:Vec<(String, u64)>=Vec::with_capacity(WORK_CHUNK_SIZE);
                    for i in 0..WORK_CHUNK_SIZE{
                      results.push(self.work_miner.sorted_list_challenge(&last_hash, &prefix, num_int));
                    }

                    for (hash,nonce) in results{
                      if &(hash.as_bytes())[0..4]==prefix.as_bytes() {
                        (*self.nonce_sender.lock().unwrap()).send(nonce.to_string()).unwrap();
                          println!("Nonce sent to main thread!.");
                          found=true;
                        break;
                      }
                    }
                },
                ThreadAssignment::ReverseSortedList(last_hash, prefix, num_int, challenge_id)=>{
                  let mut results:Vec<(String, u64)>=Vec::with_capacity(WORK_CHUNK_SIZE);
                  for i in 0..WORK_CHUNK_SIZE{
                    results.push(self.work_miner.reverse_challenge(&last_hash, &prefix, num_int));
                  }

                  for (hash,nonce) in results{
                    if &(hash.as_bytes())[0..4]==prefix.as_bytes() {
                      (*self.nonce_sender.lock().unwrap()).send(nonce.to_string()).unwrap();
                        println!("Nonce sent to main thread!.");
                        found=true;
                      break;
                    }
                  }
                },
                ThreadAssignment::ShortestPath(last_hash, prefix, size, num_blockers, challenge_id)=>{
                  let mut results:Vec<Option<(String, u64)>>=Vec::with_capacity(WORK_CHUNK_SIZE);
                  for i in 0..WORK_CHUNK_SIZE{
                    results.push(self.work_miner.shortest_path_challenge(&last_hash, &prefix, size, num_blockers, 100));
                  }

                  for opt in results{
                    match opt{
                      Some((h,n))=>{
                        if &(h.as_bytes())[0..4]==prefix.as_bytes() {
                          (*self.nonce_sender.lock().unwrap()).send(n.to_string()).unwrap();
                            println!("Nonce sent to main thread!.");
                            found=true;
                          break;
                        }
                      },
                      _=>{}
                    }
                  }
                }
               }
             }
           }
        ()
    }

}
