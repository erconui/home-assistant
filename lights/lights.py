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
    #self.listen_state(self.dance_start, "input_boolean.dance", new="on")
    #self.listen_state(self.dance_stop, "input_boolean.dance", new="off")
    #self.listen_state(self.room_toggle, "input_boolean.theater_lights")
    #self.listen_state(self.room_toggle, "input_boolean.kitchen_lights")
    #self.listen_state(self.room_toggle, 'input_boolean.fae_lights')
    #self.listen_state(self.room_toggle, 'input_boolean.ocean_lights')

    self.listen_state(self.dance, "input_select.dance")
    for room in self.rooms:
      toggle = f"input_boolean.{room}_lights"
    #  self.log(toggle)
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
        if self.commands['dance'] in (room,'full'): self.commands['dance'] = 'none'
        percentage = float(self.get_state(f"input_number.{room}_brightness")) / 100.
        self.log(f"Percentage: {percentage}")

      for light in lights:
        # self.log(f"command is {command} {self.commands[command]}")
        light_state = self.get_state(f"light.{light}", attribute='all')
        if light_state is None: continue
        self.log(f"light {light} {light_state}")
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
            self.update_light(light, percent=0, total_duration=3, dur=.1,
                              color_temp=238, color_temp_old=color_temp_old,
                              brightness=brightness, brightness_old=brightness_old,
                              command=command)
        else:
            self.update_light(light, percent=0, total_duration=3, dur=.1,
                    color_temp=238,
                    brightness=int(256*percentage) if new=='on' else 0,
                    brightness_old=brightness_old, command=command)
            # self.run_in(lambda _: self.update_light(light, percent=0, total_duration=3/2, dur=.1,
            #         color_temp=238, brightness=255 if new=='on' else 0,
            #         brightness_old=self.get_state(f"light.{light}", attribute='brightness'),
            #         command=command), 1.6)
            # self.run_in(lambda _: self.update_light(light_id, percent=0, brightness=255), 1.6)

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
          #for name in self.dumb + self.smart + self.semi_smart:
          #    self.log(name)
          #    self.color_change_random(name, 30)
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

  def update_light(self, light_id, **kwargs):
    if light_id in self.dumb and self.light_active[light_id] == False:
      return
    light_state = self.get_state(f"light.{light_id}", attribute='all')
    if light_state['state'] == 'unavailable':
      if 'stale_count' not in kwargs:
        kwargs['stale_count'] = 1
      else:
        kwargs['stale_count'] += 1
      if kwargs['stale_count'] < 30:
        self.run_in(lambda _: self.update_light(light_id, **kwargs), kwargs['dur'])
      return
    else: kwargs.pop('stale_count', None)
    self.log(f"{light_id} attributes {light_state}")
    if light_state['state'] == 'off' and kwargs['brightness'] == 0:
      return
    self.log(kwargs)
    if not self.commands[kwargs['command']]: return
    hass_kwargs = {'entity_id': f"light.{light_id}"}
    if light_id in self.smart:
        if 'hs' in kwargs: hass_kwargs['hs_color'] = kwargs['hs']
        if 'rgb' in kwargs: hass_kwargs['rgb_color'] = kwargs['rgb']
        if 'color_temp' in kwargs: hass_kwargs['color_temp'] = kwargs['color_temp']
        if 'brightness' in kwargs: hass_kwargs['brightness'] = kwargs['brightness']
        if 'total_duration' in kwargs: hass_kwargs['transition'] = kwargs['total_duration']
        self.turn_on(**hass_kwargs)
        return

    percent = kwargs['percent']
    if 'hs_old' in kwargs:
      total_diff = (self.wrap_hue(kwargs['hs_old'][0],kwargs['hs'][0])**2 + (kwargs['hs'][1] - kwargs['hs_old'][1])**2)**.5
      if total_diff > 0 and light_state['state'] == 'on':
        diff = (self.wrap_hue(light_state['attributes']['hs_color'][0],kwargs['hs_old'][0])**2 + (kwargs['hs_old'][1] - light_state['attributes']['hs_color'][1]))**.5
        #percent = diff/total_diff+kwargs['dur']/kwargs['total_duration']
      hue_change = self.wrap_hue(kwargs['hs_old'][0],kwargs['hs'][0])*percent
      hass_kwargs['hs_color'] = [(kwargs['hs_old'][0] + hue_change)%360,
                                 kwargs['hs_old'][1] + (kwargs['hs'][1] - kwargs['hs_old'][1])*percent]
    elif 'hs' in kwargs: hass_kwargs['hs_color'] = kwargs['hs']
    if 'rgb_old' in kwargs:
      total_diff = ((kwargs['rgb'][0] - kwargs['rgb_old'][0])**2 + (kwargs['rgb'][1] - kwargs['rgb_old'][1])**2 + (kwargs['rgb'][2] - kwargs['rgb_old'][2])**2)**.5
      if total_diff > 0 and light_state['state'] == 'on':
        diff = ((light_state['attributes']['rgb'][0] - kwargs['rgb_old'][0])**2 + 
                (light_state['attributes']['rgb'][1] - kwargs['rgb_old'][1])**2 + 
                (light_state['attributes']['rgb'][2] - kwargs['rgb_old'][2])**2)**.5
        #percent = diff/total_diff+kwargs['dur']/kwargs['total_duration']
      hass_kwargs['rgb_color'] = [kwargs['rgb_old'][0] + (kwargs['rgb'][0] - kwargs['rgb_old'][0])*percent,
                                  kwargs['rgb_old'][1] + s(kwargs['rgb'][1] - kwargs['rgb_old'][1])*percent,
                                  kwargs['rgb_old'][2] + (kwargs['rgb'][2] - kwargs['rgb_old'][2])*percent]
    elif 'rgb' in kwargs: hass_kwargs['rgb_color'] = kwargs['rgb']
    if 'color_temp_old' in kwargs:
      total_diff = (kwargs['color_temp'] - kwargs['color_temp_old'])
      #if total_diff > 0 and light_state['state'] == 'on':
      #  percent = (light_state['attributes']['color_temp'] - kwargs['color_temp_old']) / total_diff+kwargs['dur']/kwargs['total_duration']
      hass_kwargs['color_temp'] = kwargs['color_temp_old'] + (kwargs['color_temp'] - kwargs['color_temp_old'])*percent
    elif 'color_temp' in kwargs: hass_kwargs['color_temp'] = kwargs['color_temp']
    if 'brightness_old' in kwargs:
      total_diff = (kwargs['brightness'] - kwargs['brightness_old'])
      if total_diff > 0 and light_state['state'] == 'on':
        #percent = (light_state['attributes']['brightness'] - kwargs['brightness_old']) / total_diff+kwargs['dur']/kwargs['total_duration']
        self.log(f"TESTESTESTETSE {light_id} {percent} {kwargs['brightness_old']} -> {light_state['attributes']['brightness']} -> {kwargs['brightness']}")
      hass_kwargs['brightness'] = kwargs['brightness_old'] + (kwargs['brightness'] - kwargs['brightness_old'])*percent
      self.log(f"commanded {light_id} {hass_kwargs['brightness']}")
    elif 'brightness' in kwargs: hass_kwargs['brightness'] = kwargs['brightness']

    if 'dur' in kwargs:
      hass_kwargs['transition'] = kwargs['dur']
      #kwargs['percent'] = percent
      if kwargs['percent'] < 1:
        kwargs['percent'] += kwargs['dur']/kwargs['total_duration']
        kwargs['percent'] = min(1,kwargs['percent'])
        self.run_in(lambda _: self.update_light(light_id, **kwargs), kwargs['dur'])
      else: self.light_active[light_id] = False
    self.log(f"Check {light_id} {hass_kwargs}")
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
      self.update_light(light_id,
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
              self.update_light(light_id,
                hs_old=(color_old[0],color_old[1]), hs=(color_next[0],color_next[1]),
                brightness=color_next[2], brightness_old=color_old[2],
                percent=0, dur=self.step, total_duration=duration, command='dance')
              self.run_in(lambda _: self.color_change_random(light_id, room, duration), duration+self.step*4)
          else:
              self.log("stop")
              self.log(f"{light_id} believed active")
              self.run_in(lambda _: self.color_change_random(light_id, room, duration), self.step*4)
      self.log("end of method")
