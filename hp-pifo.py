# Implements HP-PIFO algorithm in python to check inversions. 
# Compares with heirarchial PIFO in python to compare inversions with SP-PIFO

#!/usr/bin/env python3

# TODO: Try different packet ranks. Uniform, Exponential, Inverse Exponential, Poisson

import time
import random
import multiprocessing as mp
import numpy as np
import argparse

# NUM_OF_S1_QUEUES = [2, 4, 8, 16]
# NUM_OF_S2_QUEUES = [2, 4, 8, 16]

NUM_OF_S1_QUEUES = [2, 4, 8, 16]
NUM_OF_S2_QUEUES = [2, 4, 8, 16]

ITERATIONS = 1                                  # Not needed since, constant packets

class Packet:
    def __init__(self, rank, id) -> None:
        self.rank = rank
        self.pktid = id                         # Unix time in seconds
    
    def __repr__(self) -> str:
        return(f"Rank: {self.rank}, ID: {self.pktid}")

def generate_packet(inpf, inp_q):
    """Read packets from file and put in input q"""
    with open(inpf, 'r') as f:
        total_pkts, max_rank = map(int, f.readline().strip().split(","))
        for _ in range(total_pkts):
            id, rank = f.readline().strip().split(" ")
            pkt = Packet(rank=int(rank), id=float(id))
            inp_q.put(pkt, block=True)

        """Last sentinel packet"""
        inp_q.put(Packet(-1, -1), block=True)
        print("Sent last packet")

def consume_packet(s1_qs, s2_qs):
    """Consume packet from s1 qs as well, except the first q"""
    while True:
        selected_q = None

        """Select a queue from the second stage first (has highest priority)"""
        for q in s2_qs:
            if not q.empty():
                selected_q = q
                break
        
        """If second stage q is not selected, then choose from first stage, except the 1st q in first stage"""
        if selected_q == None:
            for i, q in enumerate(s1_qs):              # First q has highest priority
                if i == 0:
                    continue

                if not q.empty():
                    selected_q = q
                    break
                
        if selected_q:
            pkt = selected_q.get()
            # print(f"Consumed {pkt}")
            if pkt.pktid == -1:
                # print("Received last packet")
                break

def stage1_sppifo(inpq, s1_qs, s2_qs, avg_inv, avg_inv_per_rank):
    """
        The bounds are reversed. 
        First bound for lowest priority q, last bound for highest priority q
        Allows to access list without the need to reverse
    """
    bounds = [0 for _ in range(len(s1_qs))]
    
    inversions = 0
    
    # inversions_per_rank = [0 for _ in range(max_rank)]
    
    while True:
        pkt = inpq.get()
        if pkt.pktid == -1:
            s1_qs[-1].put(pkt)                  # Put into lowest priority q
            s1_qs[0].put(Packet(-2, -2))                  # Indicate s2 that last packet arrived
            print("S1 rxd last packet")
            break

        # PUSHUP STAGE
        """Note. 
            First q has highest priority; last q has the lowest priority
            Corresponding bounds are other way around
        """
        # print("S1", pkt.rank)
        """Temp variable needed since bounds are updated and thus can't detect inversions."""
        # TODO: Can merge pushup and pushdown stage so that this is not needed.
        bound_1 = bounds[-1]

        for i, bound in enumerate(bounds):
            """Check which q to fit the pkt in. Or if, it's the highest priority q; in this case, fit packet there"""
            if pkt.rank >= bound or i == len(s1_qs)-1:
                bounds[i] = pkt.rank
                """Put packet in correst q. index is a mapping from bounds list to qs list"""
                s1_qs[len(s1_qs)-i-1].put(pkt)
                break
        # print("S1", bounds)
        
        # PUSHDOWN STAGE
        """If an inversion is detected"""
        if pkt.rank < bound_1:
            # print("S1 inversion")
            inversions += 1
            # inversions_per_rank[pkt.rank] += 1
            avg_inv_per_rank[pkt.rank] += 1
            cost = bounds[-1] - pkt.rank
            for i, bound in enumerate(bounds):
                """Update all bounds, except corresponding to highest priority q since it is updated in pushup stage"""
                if i != len(s1_qs)-1:
                    bounds[i] = bounds[i] - cost
    
    # print(f"Inversions: {inversions}. Max rank: {rank}")
    avg_inv.value += inversions
    # with open(DIST_TYPE + "_inv_per_rank.csv", 'a') as f:
    #     f.write(f"MR: {rank}, NQs: {num_qs}\n")
    #     for item in inversions_per_rank:
    #         f.write(f"{item} ")
    #     f.write("\n")

def stage2_sppifo(s1_qs, s2_qs, avg_inv, avg_inv_per_rank):
    bounds = [0 for _ in range(len(s2_qs))]
    inversions = 0

    """Only take packets from highest priority q in s1"""
    inpq = s1_qs[0]

    while True:
        pkt = inpq.get()
        if pkt.pktid == -2:
            # s2_qs[-1].put(pkt)
            print("S2 rxd last packet")
            break

        # PUSHUP
        # print("S2", pkt.rank)
        bound_1 = bounds[-1]
        for i, bound in enumerate(bounds):
            if pkt.rank >= bound or i == len(s2_qs)-1:
                bounds[i] = pkt.rank
                s2_qs[len(s2_qs)-i-1].put(pkt)
                break
        # print("S2", bounds)


        # PUSHDOWN
        if pkt.rank < bound_1:
            # print("S2 inversion")
            inversions += 1
            avg_inv_per_rank[pkt.rank] += 1
            cost = bounds[-1] - pkt.rank
            for i, bound in enumerate(bounds):
                if i != len(s1_qs)-1:
                    bounds[i] = bounds[i] - cost

    avg_inv.value += inversions

if __name__ == "__main__":
    random.seed(0)
    np.random.seed(0)

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", help="Input packet file", type=str)
    parser.add_argument("-o", help="Ouput file (CSV)", type=str)

    args = parser.parse_args()

    s1_avg_inv = mp.Value("i", 0)
    s2_avg_inv = mp.Value("i", 0)

    with open(args.o, 'w') as f:
        f.write("Num S1 Qs, Num S2 Qs, Max Rank, S1 Norm. Mean Inversions, S2 Norm. Mean Inversions\n")

    with open(args.i, 'r') as f:
        max_packets, max_rank = map(int, f.readline().strip().split(","))

    for num_s1_qs in NUM_OF_S1_QUEUES: 
        for num_s2_qs in NUM_OF_S2_QUEUES:
            s1_avg_inv.value = 0
            s2_avg_inv.value = 0

            s1_avg_inv_per_rank = mp.Array("i", max_rank)
            s2_avg_inv_per_rank = mp.Array("i", max_rank)

            for _ in range(ITERATIONS):
                inp_q = mp.Queue(maxsize=1)

                s1_qs = [mp.Queue() for _ in range(num_s1_qs)]
                s2_qs = [mp.Queue() for _ in range(num_s2_qs)]

                packet_generator = mp.Process(target=generate_packet, args=(args.i, inp_q))
                s1_sppifo_proc = mp.Process(target=stage1_sppifo, args=(inp_q, s1_qs, s2_qs, s1_avg_inv, s1_avg_inv_per_rank))
                s2_sppifo_proc = mp.Process(target=stage2_sppifo, args=(s1_qs, s2_qs, s2_avg_inv, s2_avg_inv_per_rank))
                packet_consumer = mp.Process(target=consume_packet, args=(s1_qs, s2_qs))

                packet_generator.start()
                s1_sppifo_proc.start()
                s2_sppifo_proc.start()
                packet_consumer.start()

                if not packet_generator.join():
                    print(f"{packet_generator.pid}: {packet_generator.name} packet_generator terminated.")
                    pass
                
                if not packet_consumer.join():
                    print(f"{packet_consumer.pid}: {packet_consumer.name} packet_consumer terminated.")
                    pass

                if not s1_sppifo_proc.join():
                    print(f"{s1_sppifo_proc.pid}: {s1_sppifo_proc.name} s1_sppifo_proc terminated")
                    pass
            
                if not s2_sppifo_proc.join():
                    print(f"{s2_sppifo_proc.pid}: {s2_sppifo_proc.name} s2_sppifo_proc terminated")
                    pass

                # inp_q.close()
                # for q in out_qs:
                #     q.close()
            with open(args.o, 'a') as f:
                # TODO: In s2, normalize by total no. of packets or only the packets that were in the s2?
                f.write(f"{num_s1_qs}, {num_s2_qs}, {max_rank}, {((s1_avg_inv.value/ITERATIONS)/max_packets):.3f}, {((s2_avg_inv.value/ITERATIONS)/max_packets):.3f}\n")

            # TODO: How to calculate avg inversion per rank. Would there be inversions in stage 1? Yes, but for highest priority q
            # But do they matter? You want to check the inversions when packets go out.
            """
            with open("inv_per_rank.csv", 'a') as f:
                f.write(f"MR: {max_rank}, S1_qs: {num_s1_qs}, S2_qs: {num_s2_qs}\n")
                for item in avg_inv_per_rank:
                    f.write(f"{item} ")
                f.write("\n")
            """
