import sys
from matplotlib import pyplot as plt

# Check if the filename is provided
if len(sys.argv) < 2:
    print("Usage: ./pkt-gen-hist.py <filename>")
    sys.exit(1)

# Get the filename from the command line
filename = sys.argv[1]

# Read the ranks from the specified file
ranks = []
max_rank = None
max_packets = None
with open(filename, 'r') as f:
    max_packets, max_rank = map(int, f.readline().strip().split(","))
    for _ in range(max_packets):
        id, rank = f.readline().strip().split(" ")
        ranks.append(int(rank))

# print(ranks)

# Create the histogram with integer bins and aligned bars
plt.hist(x=ranks, bins=range(0, max_rank + 2), rwidth=0.7, align='left')
plt.xlabel('Ranks')
plt.ylabel('Frequency')
plt.title('Histogram of Ranks')

# Set x-axis ticks to integers
plt.xticks(range(0, max_rank + 1, 1))  # Adjust the step size as needed

plt.show()
