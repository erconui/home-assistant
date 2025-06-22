from lifxlan import LifxLAN
import requests
import sys
from time import sleep
# hue
WALL=1
FLOOR=2
TREE=3
KITCHEN=4
HUE_LIGHTS = [WALL,FLOOR,TREE]

def galaxy(lifx,i):
    duration = 1*60
    lights = lifx.get_lights()
    mylights = {}
    for light in lights:
        mylights[light.get_label()] = light;
    colors = [
        (63859, 46863, 43695, 3500),
        (26, 49207, 38525, 3500),
        (2304, 52376, 37927, 3500),
        (833, 53595, 38763, 3500),
        (204, 54116, 39121, 3500),
        (51968, 65535, 46958, 3500),
        (10086, 63267, 46792, 3500),
        ]
    # for i in range(3,6):
    #     mylights["Couch"].set_color(colors[i],duration=duration)
    #     sleep(duration)
    mylights["Couch"].set_color(colors[i])#,duration=5*60*100)


def changeStandard(lifx, setting, transition=4):
    if setting in ["day","dawn"]:
        bri = 254
        on = "true"
        lifxOn = True
        lifxColor=[0,0,65535,4800]
    else:
        bri = 0
        on = "false"
        lifxOn = False
        lifxColor=[0,0,0,4800]
    lifx.set_color_all_lights(lifxColor,duration=transition*100)
    lifx.set_power_all_lights(lifxOn, duration=transition*100)

    url_base = "http://192.168.0.22/api/iXgpcEgd8mlX5Nm2CIhfgQaFEPHIaxB-SsrgDxyR"
    for i in HUE_LIGHTS:
        url = "%s/lights/%d/state" %(url_base, i)
        print(url)
        data = '{"on": %s, "bri": %d, "hue":33585,"sat":133,"transitiontime":%d}'%(on,bri,transition)
        r = requests.put(url, data=data)
    data = '{"on": %s, "bri": %d, "hue":41441,"sat":37, "transitiontime":%d}' % (on,bri,transition)
    url = "%s/lights/%d/state" %(url_base, KITCHEN)
    r = requests.put(url, data=data)


if __name__ == "__main__":
    args = sys.argv[1:]
    print(args)
    transitiontime = 4
    lifx = LifxLAN()
    if args[0] in ["dawn", "day", "dusk", "night"]:
        if args[0] in ["dawn","dusk"]:
            transitiontime=60*30
        changeStandard(lifx, args[0], transitiontime)
    else:
        galaxy(lifx, int(args[0]))
