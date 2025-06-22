import sys

filename = sys.argv[1]
data = []
with open(filename, 'r') as f:
	lines = f.readlines()
	for line in lines:
		info = line[1:-1].split(', ')
		print([info[0], info[1], info[2]])

