from lifxlan import LifxLAN
from time import sleep

lifx = LifxLAN()
lights = lifx.get_lights()
ceiling = None
for light in lights:
	print(light.get_color())
	# if light.get_label() == "Ceiling Lamp":
	# 	ceiling = light

# for i in range(60*60*1000):
# 	sleep(.001)
# 	print(ceiling.get_color())
