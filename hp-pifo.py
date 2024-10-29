# Implements HP-PIFO algorithm in python to check inversions. 
# Compares with heirarchial PIFO in python to compare inversions with SP-PIFO

#!/usr/bin/env

# TODO: Try different packet ranks. Uniform, Exponential, Inverse Exponential, Poisson

import time
import random
import multiprocessing as mp
import numpy as np

NUM_OF_QUEUES = [2, 4, 8, 16]
# NUM_OF_QUEUES = [8]

MAX_RANKS = [10, 20, 40, 80, 160, 320, 640, 1000]
# MAX_RANKS = [80]

# DIST_TYPE = "unif"                                      # unif, exp, invexp, pois
DIST_TYPE = "pois"

MAX_PACKETS = 100000
ITERATIONS = 1

class Packet:
    def __init__(self, rank, id) -> None:
        self.rank = rank
        self.pktid = id                         # Unix time in seconds
    
    def __repr__(self) -> str:
        return(f"Rank: {self.rank}, ID: {self.pktid}")

def generate_packet(inp_q, dist_type, max_rank):
    total_pkts = 0
    with open(DIST_TYPE + "_hist.txt", 'w') as hist_file:
        if dist_type == "unif":
            while total_pkts < MAX_PACKETS:
                rank = random.randint(1, max_rank)               # MAX value subject to change
                id = time.time()
                pkt = Packet(rank, id)
                inp_q.put(pkt, block=True)                  # Block until a free slot is available.
                total_pkts += 1
                hist_file.write(f"{rank} ")
                # time.sleep(0.0001)
            inp_q.put(Packet(-1, -1), block=True)           # Send a sentinel pkt
            # print("Generator sent a SENTINEL packet")
        elif dist_type == "exp":
            pass
        elif dist_type == "invexp":
            pass
        elif dist_type == "pois":
            lam = max_rank//2
            while total_pkts < MAX_PACKETS:
                # Generate packets between max rank and 1
                rank = np.random.poisson(lam=lam)
                while rank < 1 or rank > max_rank:
                    rank = np.random.poisson(lam=lam)

                id = time.time()
                pkt = Packet(rank, id)
                inp_q.put(pkt, block=True)
                total_pkts += 1
                hist_file.write(f"{rank} ")
            inp_q.put(Packet(-1, -1), block=True)
        else:
            print(f"Unknown distribution {dist_type}")
            exit(1)

def consume_packet(out_qs):
    while True:
        # TODO (DONE): figure out which Q to consume. 
        selected_q = None
        for q in out_qs:              # Last q has highest priority
            if not q.empty():
                selected_q = q
                break
                
        if selected_q:
            pkt = selected_q.get()
            # print(pkt)
            if pkt.pktid == -1:
                # print("Received last packet")
                break

def sppfio(inpq, outqs, rank, avg_inv, num_qs, avg_inv_per_rank):
    # TODO: put packet in designated Q
    # Bounds are reversed. 1st bound is for lowest priority q, last bound is for highest priority q
    bounds = [0 for _ in range(num_qs)]
    inversions = 0
    inversions_per_rank = [0 for _ in range(rank)]
    
    while True:
        pkt = inpq.get()
        if pkt.pktid == -1:
            outqs[-1].put(pkt)                  # Put into lowest priority q
            break

        # PUSHUP
        # Note. The last q in outqs is the highest priority, with first q having lowest priority
        # print(pkt.rank)
        bound_1 = bounds[-1]
        for i, bound in enumerate(bounds):
            if pkt.rank >= bound or i == num_qs-1:
                bounds[i] = pkt.rank
                outqs[num_qs-i-1].put(pkt)
                break
        # print(bounds)
        
        # PUSHDOWN
        if pkt.rank < bound_1:
            # print("inversion")
            inversions += 1
            inversions_per_rank[pkt.rank] += 1
            avg_inv_per_rank[pkt.rank] += 1
            cost = bounds[-1] - pkt.rank
            for i, bound in enumerate(bounds):
                if i != num_qs-1:
                    bounds[i] = bounds[i] - cost
    
    # print(f"Inversions: {inversions}. Max rank: {rank}")
    avg_inv.value += inversions
    with open(DIST_TYPE + "_inv_per_rank.csv", 'a') as f:
        f.write(f"MR: {rank}, NQs: {num_qs}\n")
        for item in inversions_per_rank:
            f.write(f"{item} ")
        f.write("\n")


if __name__ == "__main__":
    random.seed(0)
    np.random.seed(0)
    avg_inv = mp.Value("i", 0)
    with open(DIST_TYPE + ".csv", 'w') as f:
        f.write("Num Qs, Max Rank, Norm. Mean Inversions\n")

    for num_qs in NUM_OF_QUEUES:
        for max_rank in MAX_RANKS:  
            avg_inv.value = 0
            avg_inv_per_rank = mp.Array("i", max_rank)
            for _ in range(ITERATIONS):
                inp_q = mp.Queue(maxsize=1)
                out_qs = [mp.Queue() for _ in range(num_qs)]

                packet_generator = mp.Process(target=generate_packet, args=(inp_q, DIST_TYPE, max_rank))
                packet_consumer = mp.Process(target=consume_packet, args=(out_qs, ))
                sp_pifo_proc = mp.Process(target=sppfio, args=(inp_q, out_qs, max_rank, avg_inv, num_qs, avg_inv_per_rank))

                sp_pifo_proc.start()
                packet_generator.start()
                packet_consumer.start()

                if not packet_generator.join():
                    # print(f"{packet_generator.pid}: {packet_generator.name} packet_generator terminated.")
                    pass
                
                if not packet_consumer.join():
                    # print(f"{packet_consumer.pid}: {packet_consumer.name} packet_consumer terminated.")
                    pass

                if not sp_pifo_proc.join():
                    # print(f"{sp_pifo_proc.pid}: {sp_pifo_proc.name} sp_pifo_proc terminated")
                    pass

                # inp_q.close()
                # for q in out_qs:
                #     q.close()
            with open(DIST_TYPE + ".csv", 'a') as f:
                f.write(f"{num_qs}, {max_rank}, {((avg_inv.value/ITERATIONS)/MAX_PACKETS):.3f}\n")

            with open(DIST_TYPE + "_inv_per_rank.csv", 'a') as f:
                f.write(f"MR: {max_rank}, NQs: {num_qs}\n")
                for item in avg_inv_per_rank:
                    f.write(f"{item} ")
                f.write("\n")
