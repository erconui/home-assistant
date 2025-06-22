from lifxlan import LifxLAN
from time import sleep

lifx = LifxLAN()
ceiling = lifx.get_lights()[0]
ceiling.set_label("Ceiling Lamp")
print(ceiling.get_label())
ceiling.set_power(65535)
with open("galaxy.txt", "r") as f:
	lines = f.readlines()
	for line in lines:
		hue, saturation, brightness, kelvin = line.strip()[1:-1].split(", ")
		#print(hue,saturation,brightness,kelvin)
		ceiling.set_color([hue,saturation,brightness,kelvin], .01)
		sleep(.01)
		#ceiling.set_color(
		#print(line)

#for i in range(10*60*10):
#	sleep(.1)
#	print(ceiling.set_color())
