import sys
from matplotlib import pyplot as plt

# Check if the filename is provided
if len(sys.argv) < 2:
    print("Usage: python script.py <filename>")
    sys.exit(1)

# Get the filename from the command line
filename = sys.argv[1]

# Read the ranks from the specified file
ranks = []
with open(filename, 'r') as f:
    ranks = [int(x) for x in f.readline().strip().split(" ")]

max_rank = max(ranks)
print(ranks)

# Create the histogram
plt.hist(x=ranks, bins=max_rank, rwidth=0.7)
plt.xlabel('Ranks')
plt.ylabel('Frequency')
plt.title('Histogram of Ranks')
plt.show()
