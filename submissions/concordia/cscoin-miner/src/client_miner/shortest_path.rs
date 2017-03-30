use rand::{Rng, SeedableRng};
use mersenne_twister::MersenneTwister;
use std::cmp::Ordering;
use std::cmp;
use std::collections::BinaryHeap;
use fnv::FnvHashSet;
use fnv::FnvHashMap;
use itertools::Itertools;
use std::fmt;
use std::usize;





#[derive(Eq, PartialEq, Copy, Clone)]

struct State {
    cost_pos: (usize,usize)
}

impl Ord for State {
    fn cmp(&self, other: &State) -> Ordering {
        other.cost_pos.cmp(&self.cost_pos)
    }
}

impl PartialOrd for State {
    fn partial_cmp(&self, other: &State) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

pub struct Grid{
    pub size:usize,
    pub num_blockers:u64,
    pub blockers:FnvHashSet<usize>,
    pub start_pt:usize,
    pub end_pt:usize
}

impl fmt::Display for Grid {
    // This trait requires `fmt` with this exact signature.
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {

        let mut grid_str=String::new();

        // let mut start_neighbours:Vec<usize>=Vec::with_capacity(4);
        //
        // for i in self.neighbours(self.start_pt).iter(){
        //     match i {
        //         &Some(x)=>{start_neighbours.push(x)},
        //         _=>{}
        //     }
        // }

        grid_str.push_str(&self.start_pt.to_string());
        grid_str.push_str("\n ");

        for i in 0..self.size{
            grid_str.push_str(&format!("{number:>width$}", number=&i.to_string(), width=2));
        }
        for i in 0..self.size*self.size{
            if i%self.size==0 {
                grid_str.push_str("\n");
                grid_str.push_str(&format!("{number:>width$}", number=&(i/self.size).to_string(), width=2));
            }
            if i==self.end_pt{
                grid_str.push_str("e ");
            } else if i==self.start_pt{
                grid_str.push_str("s ");
            } else if self.blockers.contains(&i){
                grid_str.push_str("x ");
            } else{
                grid_str.push_str("  ");
            }
        }
        write!(f, "{}", grid_str)

    }

}


impl Grid{

    pub fn new(sz:usize, nb:u64)->Grid
    {
        Grid{
            size:sz,
            num_blockers:nb,
            blockers:FnvHashSet::with_capacity_and_hasher(sz*4+(nb as usize), Default::default()),
            start_pt:0,
            end_pt:0
        }

    }

    pub fn neighbours(&self, pt:usize)->[Option<usize>;4]
    {
        let neighbours:[Option<usize>;4]=[self.maybe_neighbour(pt.checked_add(self.size).unwrap_or(self.size*self.size)),
                                          self.maybe_neighbour(pt.checked_sub(self.size).unwrap_or(0)),
                                          self.maybe_neighbour(pt.checked_add(1).unwrap_or(self.size*self.size)),
                                          self.maybe_neighbour(pt.checked_sub(1).unwrap_or(0))];

        return neighbours;
    }

    //ONLY WORKS FOR NON-BOUNDARY POINTS TO SAVE TIME
    //Should not be called on walls
    pub fn maybe_neighbour(&self, pt:usize)->Option<usize>
    {
        if pt<self.size*self.size && !self.blockers.contains(&pt){
            return Some(pt);
        }else{
            return None;
        }
    }

    pub fn at_mod(&self, x:usize, y:usize)->usize
    {
        return (x%self.size)*self.size+y%self.size;
    }

    pub fn at(&self, x:usize, y:usize)->Option<usize>
    {
        if x<self.size && y<self.size{
            return Some(x*self.size+y);
        }else{
            return None;
        }
    }

    //Does not check for start/end points, since they should not be initialized when this is called
    fn place_walls(&mut self)
    {
        for i in 0..(self.size){
            self.blockers.insert(i);
            self.blockers.insert((self.size-1)*self.size+i);
            self.blockers.insert(self.size*i+self.size-1);
            self.blockers.insert(self.size*i);
        }
    }

    pub fn distance_h(&self, start:usize, goal:usize)->usize
    {
         (cmp::max(start%self.size, goal%self.size)-cmp::min(start%self.size, goal%self.size))
         +(cmp::max(start/self.size, goal/self.size)-cmp::min(start/self.size, goal/self.size))
    }


    pub fn populate(&mut self, random:&mut MersenneTwister)
    {

        self.place_walls();

        let mut x = random.next_u64() as usize;
        let mut y = random.next_u64() as usize;

        //Check if not wall
        while (x%self.size)%(self.size-1)==0 || (y%self.size)%(self.size-1)==0{
            x=random.next_u64() as usize;
            y=random.next_u64() as usize;
        }

        self.start_pt=self.at_mod(x,y);
        self.blockers.insert(self.start_pt);

        let mut found_end=false;
        while !found_end{
            x=random.next_u64() as usize;
            y=random.next_u64() as usize;
            found_end=!self.blockers.contains(&self.at_mod(x,y));
        }

        self.end_pt=self.at_mod(x,y);

        for i in 0..self.num_blockers{
            let loc = self.at_mod(random.next_u64() as usize,random.next_u64() as usize);
            if loc!=self.end_pt{
                self.blockers.insert(loc);
            }
        }
    }

}


pub fn a_star(_grid:&Grid)->Option<(FnvHashMap<usize,Option<usize>>,usize)>
{
    let mut frontier=BinaryHeap::new();

   let mut came_from=FnvHashMap::default();
   let mut cost_so_far=FnvHashMap::default();

   frontier.push(State{ cost_pos:(0, _grid.start_pt)});
   came_from.insert(_grid.start_pt, None);

   cost_so_far.insert(_grid.start_pt, 0);

   //println!("{}:{}", (_grid.end_pt%_grid.size).to_string(),(_grid.end_pt/_grid.size).to_string());

   while let Some(State { cost_pos }) = frontier.pop() {

       // Alternatively we could have continued to find all shortest paths

       let (cost, position) = cost_pos;

       //println!("{}:{}", (position%_grid.size).to_string(),(position/_grid.size).to_string());

       if position == _grid.end_pt {

           //println!("Found it!");

           return Some((came_from,cost));

       }

       // For each node we can reach, see if we can find a way with

       // a lower cost going through this node

       for point in &_grid.neighbours(position) {

           match point{

               &Some(pt)=>{

                   let new_cost = cost_so_far[&position] + 1;

                   if !cost_so_far.contains_key(&pt) || cost_so_far[&pt]>new_cost{

                       cost_so_far.insert(pt, new_cost);

                       //let next_state=State{cost: new_cost+_grid.distance_h(pt,_grid.end_pt), position: pt};

                       let next_state=State{cost_pos: (new_cost, pt)};

                       frontier.push(next_state);

                       came_from.insert(pt, Some(position));

                   }
               },

               &None=>{}
           }
       }
   }

   None
}

pub fn reconstruct_path(_grid:&Grid, came_from: FnvHashMap<usize,Option<usize>>, cost: usize)->String
{
    let mut current:Option<usize>=Some(_grid.end_pt);

    let mut path : Vec<usize>=Vec::with_capacity((cost+1)*2);

    while current!=None {
        match current{
            Some(pt)=>{
                path.push(pt%_grid.size);
                path.push(pt/_grid.size);
                current=came_from[&pt];
            }
            None=>{break;}
        }
    }

    path.reverse();

    return path.clone().iter().join("");
}
