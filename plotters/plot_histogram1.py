import sys
from matplotlib import pyplot as plt
from io import StringIO

# Check if the filename is provided
if len(sys.argv) < 2:
    print("Usage: python script.py <filename>")
    sys.exit(1)

# Get the filename from the command line
filename = sys.argv[1]

# Read the ranks from the specified file
ranks = []
content = None
with open(filename, 'r') as f:
    content = f.read()

# Read data into dictionary from file
data = {}
file = StringIO(content)

lines = file.readlines()
for i in range(0, len(lines), 2):  # Step by 2 lines (one for MR/NQs, one for values)
    # Parse MR and NQs
    header = lines[i].strip()
    mr_value = int(header.split("MR: ")[1].split(",")[0])
    nqs_value = int(header.split("NQs: ")[1])
    
    # Parse y-values
    y_values = list(map(float, lines[i + 1].strip().split()))
    data[(mr_value, nqs_value)] = y_values

uniq_mr_values = sorted({key[0] for key in data.keys()})
fig, axs = plt.subplots(len(uniq_mr_values), 1)

for idx, MR in enumerate(uniq_mr_values):
    ax = axs[idx]
    for (mr_value, nqs_value), y_values in data.items():
        if mr_value == MR:
            x_values = list(range(MR))
            ax.plot(x_values, y_values, label=f"NQs: {nqs_value}")
    
    ax.set_title(f'MR = {MR}', y=0.75, loc="left")
    ax.set_xlabel('X-axis')
    ax.grid(True)
    ax.legend()

fig.supylabel('Y-axis')
plt.tight_layout()
plt.show()

# # Plotting data from file
# for MR in {key[0] for key in data.keys()}:
#     plt.figure(figsize=(10, 6))
#     for (mr_value, nqs_value), y_values in data.items():
#         if mr_value == MR:
#             x_values = list(range(MR))
#             plt.plot(x_values, y_values, marker='o', label=f'NQs: {nqs_value}')

#     plt.title(f'Plot for MR = {MR}')
#     plt.xlabel('X-axis')
#     plt.ylabel('Y-axis')
#     plt.legend()
#     plt.grid(True)
#     plt.show()


