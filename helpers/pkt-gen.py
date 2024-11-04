#!/usr/bin/env python3

import argparse
import numpy as np
import time

def gen_exp(outf, max_packets, max_rank):
    pass

def gen_unif(outf, max_packets, max_rank):
    total_pkts = 0
    with open(outf, 'w') as f:
        f.write(f"{max_packets}, {max_rank}\n")
        while total_pkts < max_packets:
            rank = np.random.randint(1, max_rank)
            id = time.time()
            pkt = (id, rank)
            f.write(f"{(pkt[0]):.6f} {pkt[1]}\n")

            total_pkts += 1

def gen_pois(outf, max_packets, max_rank):
    total_pkts = 0
    lam = max_rank//2
    with open(outf, 'w') as f:
        f.write(f"{max_packets}, {max_rank}\n")
        while total_pkts < max_packets:
            rank = np.random.poisson(lam=lam)
            while rank < 1 or rank > max_rank:
                rank = np.random.poisson(lam=lam)

            id = time.time()
            pkt = (id, rank)
            f.write(f"{(pkt[0]):.6f} {pkt[1]}\n")

            total_pkts += 1

if __name__ == "__main__":
    np.random.seed(0)
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', help="Distribution: unif, pois. More will be added.", type=str)
    parser.add_argument('-o', help="Output file", type=str)
    parser.add_argument('-mp', help="Max packets to generate", type=int)
    parser.add_argument('-mr', help="Max packet ranks", type=int)

    args = parser.parse_args()

    if args.d == "exp":
        gen_exp(args.o, args.mp, args.mr)
    elif args.d == "unif":
        gen_unif(args.o, args.mp, args.mr)
    elif args.d == "pois":
        gen_pois(args.o, args.mp, args.mr)
    else:
        print("Incorrect distribution.")
        exit(1)

    # Parse arguments for distribution of packets

