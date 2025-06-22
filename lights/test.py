from lifxlan import LifxLAN
from time import sleep
lifx = LifxLAN()
ceiling = lifx.get_lights()[0]
sleep(20 * 60)
ceiling.set_power(0)
