import appdaemon.plugins.hass.hassapi as hass
from random import randint
from time import sleep
from copy import deepcopy

class Lights(hass.Hass):

  def initialize(self):
    self.log("Hello from AppDaemon Lights")
    self.step = 1
    self.defineColors()
    self.defineLights()

    self.commands = {'theater-on':False, 'theater-off':False, 'kitchen-on':False,'kitchen-off':False,'breach':False, 'dance': 'none'}
    thermostat = self.get_state('climate.orem_property')
    self.log(f"thermostat state {thermostat}")

    self.listen_state(self.dance, "input_select.dance")
    for room in self.rooms:
      toggle = f"input_boolean.{room}_lights"
      self.listen_state(self.room_toggle, toggle)
      self.listen_state(self.room_toggle, f"input_number.{room}_brightness")
    self.listen_state(self.breach, "climate.orem_property")
    self.listen_state(self.breach, "input_boolean.dooropen")
    self.log("Lights initialized")

  def defineColors(self):
    #self.colors = [[36,36,255],[255,36,145],[109,255,218],[127,0,255],[0,255,254],[254,0,255],[255,109,145],[63,0,255],[109,255,182],[255,36,91],[127,255,0]]
    #,,teal,purple,
    self.hsb = [
      [240, 85.881,99], #light indigo
      [330.133,85.881,76], #redish pink
      [164.792,57.255,51], # teal
      [269.878,100,71], # purple
      [179.761,100,71], # teal
      [299.761,100,61], # violet
      [345.102,57.086,66], #pink
      [254.821,100,66], # indigo
      [149.999,57.255,71], # ocean green
      [344.927,85.881,48], # redish pink
      [90.117,100,64] # forest green
    ]
    for idx in range(len(self.hsb)):
      self.hsb[idx][-1] /= .5
    self.neutral = [26.743, 31.347]
    self.breached = [360,100,255]
    self.temp_alert = [272.932,100,255]

  def defineLights(self):
    self.dumb = ['theater_fl', 'theater_fr', 'theater_cl', 'theater_cr', 'theater_bl', 'theater_br',
                        'wiz1','wiz2','wiz3','wiz4','wiz5','wiz6','wiz7','wiz8', 'bed1', 'bed2',
                        'ocean1', 'ocean2', 'ocean3', 'ocean4']#wiz/tuya
    self.smart= ['headboard', 'floor', 'stairs', 'island', 'island1', 'island2', 'patio1', 'patio2', 'lantern', 'sconcel', 'sconcer'] #lifx/hue
    self.semi_smart = ['hydralisk_right_eye', 'hydralisk_left_eye', 'hydralisk_right_jaw','hydralisk_left_jaw']#esphome

    #rooms
    self.rooms = {'theater': self.dumb[:6] + self.smart[:2],
                  'kitchen': self.dumb[6:14] + self.smart[3:6],# + self.semi_smart
                  'patio': self.smart[6:8],
                  'fae': self.dumb[14:16] + [self.smart[8]],
                  'ocean': self.dumb[16:] + self.smart[9:]}
    for room in self.rooms:
        self.log(f"Initialized {room}: {*self.rooms[room],}")
    self.light_active = {}
    for room in self.rooms:
        for light in self.rooms[room]:
            self.light_active[light] = False

  def breach(self, entity, attribute, old, new, kwargs):
      # self.log(f"thermostat state {entity} {new}")
      door_open = self.get_state('input_boolean.dooropen')
      thermostat = self.get_state('climate.orem_property')
      fortress = self.get_state('input_boolean.secure')
      self.log(f"evaluate breach door {door_open} thermostat {thermostat} fortress {fortress}")
      self.commands['breach'] = True if door_open == 'on' else False
      if thermostat == 'off' and door_open == 'on':
          for light in self.smart + self.dumb:
              self.log(f"light change {light}")
              self.color_change(light, 2, self.temp_alert, command='breach')
      elif door_open == 'on':
          # fortress mode or regular door open-
          if fortress == 'on':
              for light in self.smart + self.dumb:
                  self.color_change(light, 2, self.breached, command='breach')
          else:
              kitchen = self.get_state('input_boolean.kitchen_lights')
              if kitchen == 'off':
                  self.turn_on('input_boolean.kitchen_lights')
              else:
                  self.turn_off('input_boolean.kitchen_lights')
                  sleep(.1)
                  self.turn_on('input_boolean.kitchen_lights')
      else:
          # doors are shut
          self.commands['breach'] = False
          if fortress == 'on':
              self.turn_off('input_boolean.theater_lights')
          self.turn_off('input_boolean.kitchen_lights')
          sleep(.1)
          self.turn_on('input_boolean.kitchen_lights')
          if fortress == 'on':
              self.turn_on('input_boolean.theater_lights')

  def room_toggle(self, entity, attribute, old, new, kwargs):
      room = entity.split('.')[1].split('_')[0]
      self.log(f"Toggling lights for {room} {old}->{new} {room in self.rooms}")
      if 'brightness' in entity:
        if self.get_state(f"input_boolean.{room}_lights") == 'on' and not self.commands['dance'] in (room,'full'):
          new = 'on'
        else: return
      percentage = 100
      if room in self.rooms:
        command=f"{room}-{new}"
        lights = self.rooms[room]
        self.commands[f"{room}-{new}"] = True
        self.commands[f"{room}-{new}"] = True
        if self.commands['dance'] in (room,'full'):
          self.commands['dance'] = 'none'
        percentage = float(self.get_state(f"input_number.{room}_brightness")) / 100.

      for light in lights:
        light_state = self.get_state(f"light.{light}", attribute='all')
        if light_state is None: continue
        hs_old = None
        color_temp_old = 238
        brightness_old = 0
        if light_state['state']=='on':
          if light_state['attributes']['color_mode'] == 'color_temp':
            color_temp_old = light_state['attributes']['color_temp']
          else:
            hs_old = [light_state['attributes']['hs_color'][0],
                     light_state['attributes']['hs_color'][1]]
          brightness_old = light_state['attributes']['brightness']
        brightness=int(256*percentage) if new=='on' else 0
        if light.startswith('bed') and brightness > 0: brightness = max(26, brightness)
        if hs_old is None:
          self.startUpdate(light, percent=0, total_duration=3, dur=.1,
                            color_temp=238, color_temp_old=color_temp_old,
                            brightness=brightness, brightness_old=brightness_old,
                            command=command)
        else:
          self.startUpdate(light, percent=0, total_duration=3, dur=.1,
                  color_temp=238,
                  brightness=int(256*percentage) if new=='on' else 0,
                  brightness_old=brightness_old, command=command)

  def dance(self, entity, attribute, old, new, kwargs):
    self.log("Dance state: %s -> %s",old,new)
    self.commands['dance'] = new
    if new in self.rooms:
      self.log(f"Dance active for room {new}")
      for name in self.rooms[new]:
        self.log(name)
        duration = 30 if not name.startswith('ocean') else 60
        self.light_active[name] = False
        self.color_change_random(name, new, duration)
    elif new == 'full':
      self.log('full')
      for room in self.rooms:
        for name in self.rooms:
          self.light_active[name] = False
          self.color_change_random(name, room, 30)
    else:
      self.log('off')
      self.commands['dance'] = "none"
    for room in self.rooms:
      if new != room:
        for light in self.rooms[room]:
          self.light_active[light] = False

  def wrap_hue(self, hue_old, hue_next):
    hue_diff = hue_next - hue_old
    if abs(hue_diff) > 180:
      if hue_next > hue_old:
        hue_diff = hue_diff % 360
      else:
        hue_diff = (hue_old - hue_next) - 360
    return hue_diff

  def ceil(self, val):
    if val > 0: return max(1,val)
    else: return min(-1,val)

  def isAvailable(self, light_id, state, **kwargs):
    if state != 'unavailable':
      kwargs.pop('stale_count', None)
      return True
    
    if 'stale_count' not in kwargs:
      kwargs['stale_count'] = 1
    else:
      kwargs['stale_count'] += 1
    if kwargs['stale_count'] < 30:
      self.run_in(lambda _: self.update_light(light_id, **kwargs), kwargs['dur'])
    return False

  def updateSmartLight(self, light_id, **kwargs):
    hass_kwargs = {'entity_id': f"light.{light_id}"}
    if 'hs' in kwargs: hass_kwargs['hs_color'] = kwargs['hs']
    if 'rgb' in kwargs: hass_kwargs['rgb_color'] = kwargs['rgb']
    if 'color_temp' in kwargs: hass_kwargs['color_temp'] = kwargs['color_temp']
    if 'brightness' in kwargs: hass_kwargs['brightness'] = kwargs['brightness']
    if 'total_duration' in kwargs: hass_kwargs['transition'] = kwargs['total_duration']
    self.turn_on(**hass_kwargs)

  def setHS(self, current, percent, hass_kwargs, new, old):
    if old is None:
      hass_kwargs['hs_color'] = new
      return
    hue_change = self.wrap_hue(old[0],new[0])*percent
    hass_kwargs['hs_color'] = [(old[0] + hue_change)%360,
                               old[1] + (new[1] - old[1])*percent]

  def setRGB(self, current, percent, hass_kwargs, new, old):
    if old is None:
      hass_kwargs['rgb_color'] = new
      return
    hass_kwargs['rgb_color'] = [old[0] + (new[0] - old[0])*percent,
                                old[1] + (new[1] - old[1])*percent,
                                old[2] + (new[2] - old[2])*percent]

  def setTemp(self, current, percent, hass_kwargs, new, old):
    if old is None:
      hass_kwargs['color_temp'] = new
      return
    hass_kwargs['color_temp'] = old + (new - old)*percent

  def setBrightness(self, current, percent, hass_kwargs, new, old):
    if old is None:
      hass_kwargs['brightness'] = new
      return
    hass_kwargs['brightness'] = old + (new - old)*percent

  def startUpdate(self, light_id, **kwargs):
    if self.light_active[light_id]:
      self.light_active[light_id] = False
      self.run_in(lambda _: self.startUpdate(light_id, **kwargs), self.step*2)
    else:
      self.light_active[light_id] = light_id in self.dumb
      self.update_light(light_id, **kwargs)

  def update_light(self, light_id, **kwargs):
    light = self.get_state(f"light.{light_id}", attribute='all')
    state = light['state']
    attributes = light['attributes']
    connected = self.isAvailable(light_id, state, **kwargs)
    hslog = ""
    templog = ""
    brightlog = ""
    if connected and 'hs' in kwargs and 'hs_color' in attributes: hslog = f" HS: {attributes['hs_color']}->{kwargs['hs']}"
    if connected and 'color_temp' in kwargs and 'color_temp' in attributes: templog = f" TEMP: {attributes['color_temp']}->{kwargs['color_temp']}"
    if connected and 'brightness' in kwargs and 'brightness' in attributes: brightlog = f" Brightness: {attributes['brightness']}->{kwargs['brightness']}"
    self.log(f"Update {light_id}: {'Active' if self.light_active[light_id] else 'Exit'}" +
             f" {'Connected' if connected else 'Unavailable'}" +
             f" Percent: {kwargs['percent']}%{hslog}{templog}{brightlog}")

    if light_id in self.dumb and self.light_active[light_id] == False: return
    if not connected: return
    if state == 'off' and kwargs['brightness'] == 0: return # TODO convert to function that checks if all attributes are already what they're assigned
    if not self.commands[kwargs['command']]: return
    
    if light_id in self.smart:
      self.updateSmartLight(light_id, **kwargs)
      return

    hass_kwargs = {'entity_id': f"light.{light_id}"}
    percent = kwargs['percent']
    if 'hs' in kwargs:
      self.setHS(attributes, percent, hass_kwargs, kwargs['hs'],kwargs['hs_old'] if 'hs_old' in kwargs else None)
    if 'rgb' in kwargs:
      self.setRGB(attributes, percent, hass_kwargs, kwargs['rgb'],kwargs['rgb_old'] if 'rgb_old' in kwargs else None)
    if 'color_temp' in kwargs:
      self.setTemp(attributes, percent, hass_kwargs, kwargs['color_temp'],kwargs['color_temp_old'] if 'color_temp_old' in kwargs else None)
    if 'brightness' in kwargs:
      self.setBrightness(attributes, percent, hass_kwargs, kwargs['brightness'], kwargs['brightness_old'] if 'brightness_old' in kwargs else None)

    if 'dur' in kwargs:
      hass_kwargs['transition'] = kwargs['dur']
      #kwargs['percent'] = percent
      if kwargs['percent'] < 1:
        kwargs['percent'] += kwargs['dur']/kwargs['total_duration']
        kwargs['percent'] = min(1,kwargs['percent'])
        self.run_in(lambda _: self.update_light(light_id, **kwargs), kwargs['dur'])
      else: self.light_active[light_id] = False
    self.turn_on(**hass_kwargs)

  def color_change(self, light_id, duration, color_next=None, command=None):
    light_state = self.get_state(f"light.{light_id}", attribute='all')
    if light_state['state']=='on':
      color_old = [light_state['attributes']['hs_color'][0],
                   light_state['attributes']['hs_color'][1],
                   light_state['attributes']['brightness']]
    else:
      color_old = [self.hsb[randint(0,len(self.hsb)-1)][0],
                   self.hsb[randint(0,len(self.hsb)-1)][1], 0]
    if color_next is None:
      idx = randint(0,len(self.hsb)-1)
      color_next = self.hsb[idx]
    self.log(f"change {light_id} color {color_old} -> {color_next}")
    self.startUpdate(light_id,
      hs_old=(color_old[0],color_old[1]), hs=(color_next[0],color_next[1]),
      brightness=color_next[2], brightness_old=color_old[2],
      percent=0, dur=self.step, total_duration=duration, command=command)


  def color_change_random(self, light_id, room, duration):
    if self.commands['dance'] in (room, 'full'):
      self.log(f"color change random {light_id}")
      if not self.light_active[light_id]:
        self.log("continue")
        if light_id in self.dumb: self.light_active[light_id] = True
        light_state = self.get_state(f"light.{light_id}", attribute='all')
        if light_state['state']=='on':
          color_old = [light_state['attributes']['hs_color'][0],
                       light_state['attributes']['hs_color'][1],
                       light_state['attributes']['brightness']]
        else:
          color_old = [self.hsb[randint(0,len(self.hsb)-1)][0],
                       self.hsb[randint(0,len(self.hsb)-1)][1], 0]
        idx = randint(0,len(self.hsb)-1)
        color_next = deepcopy(self.hsb[idx])
        if light_id == 'patio1' or light_id == 'patio2':
          color_next[-1] = 176
        #if light_id == 'moon':
        #    color_next[-1] = 80 + randint(0,30)
        if light_id == 'sconcer' or light_id == 'sconcel': 
          color_next[-1] = 200 + randint(0,30)
        if light_id.startswith('edison'):
          color_next[-1] *= .6
        #if light_id == 'theaterbr': color_next[-1] *= 2.0
        #if light_id in ('theaterbl', 'theatercr'): color_next[-1] *= 1.5
        #if light_id in ('theaterfl', 'theaterfr'): color_next[-1] *= .8
        
        if light_id == 'lantern':
          color_next[-1] = 200
        percentage = float(self.get_state(f"input_number.{room}_brightness")) / 100.
        color_next[-1] = int(color_next[-1] * percentage)# int(percentage*3/100.)
        self.log(f"Next color {light_id} {color_old} -> {color_next} in {duration}s")
        self.startUpdate(light_id,
          hs_old=(color_old[0],color_old[1]), hs=(color_next[0],color_next[1]),
          brightness=color_next[2], brightness_old=color_old[2],
          percent=0, dur=self.step, total_duration=duration, command='dance')
        self.run_in(lambda _: self.color_change_random(light_id, room, duration), duration+self.step*4)
      else:
        self.log("stop")
        self.log(f"{light_id} believed active")
        self.run_in(lambda _: self.color_change_random(light_id, room, duration), self.step*4)
      self.log("end of method")
