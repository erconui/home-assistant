import sys

filename = sys.argv[1]
print(filename)
with open(filename, 'r') as f:
	lines = f.readlines()
	colors = [[lines[0][1:-1].split(", "),0]]
	for line in lines[1:]:
		color = line[1:-1].split(", ")
		for i in range(len(color)):
			color[i] = color[i].strip("'")
		if color == colors[-1][0]:
			colors[-1][1] += 1
		else:
			colors.append([color,1])
	i = 0
	for color in colors:
		if color[1] > 1:
			print("%s\t%s\t%s\t%s\t%d" % (color[0][0], color[0][1], color[0][2], color[1], i))
			i = 0
		i += 1
