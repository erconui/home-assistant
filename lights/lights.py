import appdaemon.plugins.hass.hassapi as hass
from random import randint
from time import sleep

class Lights(hass.Hass):

  def initialize(self):
    self.log("Hello from AppDaemon Lights")
    self.step = 1
    self.colors = [[36,36,255],[255,36,145],[109,255,218],[127,0,255],[0,255,254],[254,0,255],[255,109,145],[63,0,255],[109,255,182],[255,36,91],[127,255,0]]
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
    self.neutral = [26.743, 31.347]
    self.breached = [360,100,255]
    self.temp_alert = [272.932,100,255]
    
    self.defineLights()

    self.commands = {'theater-on':False, 'theater-off':False, 'kitchen-on':False,'kitchen-off':False,'breach':False}
    thermostat = self.get_state('climate.orem_property')
    self.log(f"thermostat state {thermostat}")
    self.listen_state(self.dance_start, "input_boolean.dance", new="on")
    self.listen_state(self.dance_stop, "input_boolean.dance", new="off")
    self.listen_state(self.room_toggle, "input_boolean.theater_lights")
    self.listen_state(self.room_toggle, "input_boolean.kitchen_lights")
    self.listen_state(self.room_toggle, 'input_boolean.fae_lights')
    self.listen_state(self.room_toggle, 'input_boolean.ocean_lights')
    self.listen_state(self.breach, "climate.orem_property")
    self.listen_state(self.breach, "input_boolean.dooropen")
    self.log("Lights initialized")
    
  def defineLights(self):
    self.dumb_lights = ['theater_fl', 'theater_fr', 'theater_cl', 'theater_cr', 'theater_bl', 'theater_br',
                        'wiz1','wiz2','wiz3','wiz4','wiz5','wiz6','wiz7','wiz8', 'bed1', 'bed2',
                        'ocean1', 'ocean2', 'ocean3', 'ocean4']#wiz/tuya
    self.smart_lights= ['headboard', 'floor', 'stairs', 'island', 'island1', 'island2', 'patio1', 'patio2', 'lantern', 'sconcel', 'sconcer'] #lifx/hue
    self.semi_smart = ['hydralisk_right_eye', 'hydralisk_left_eye', 'hydralisk_right_jaw','hydralisk_left_jaw']#esphome
    
    #rooms
    #self.theater_lights = ['theater_fl', 'theater_fr', 'theater_cl', 'theater_cr', 'theater_bl', 'theater_br','stairs', 'headboard']
    #self.kitchen_lights = ['floor','sliding_door_light', 'island', 'wiz1', 'wiz2', 'wiz3', 'wiz4', 'wiz5', 'wiz6', 'wiz7', 'wiz8', 'patio1', 'patio2']
    #self.fae_lights = ['bed1', 'bed2', 'lantern']
    #self.ocean_lights = ['ocean1', 'ocean2', 'ocean3', 'ocean4', 'sconcel', 'sconcer']

    self.theater_lights = self.dumb_lights[:6] + self.smart_lights[:2]
    self.kitchen_lights = self.dumb_lights[6:14] + self.smart_lights[3:6]# + self.semi_smart
    self.patio_lights = self.smart_lights[6:8]
    self.fae_lights = self.dumb_lights[14:16] + [self.smart_lights[8]]
    self.ocean_lights = self.dumb_lights[16:] + self.smart_lights[9:]
    self.log('Initialized theater lights: ' + ', '.join(self.theater_lights))
    self.log('Initialized kitchen lights: ' + ', '.join(self.kitchen_lights))
    self.log('Initialized patio lights: ' + ', '.join(self.patio_lights))
    self.log('Initialized fae lights: ' + ', '.join(self.fae_lights))
    self.log('Initialized ocean lights: ' + ', '.join(self.ocean_lights))
    
  def breach(self, entity, attribute, old, new, kwargs):
      # self.log(f"thermostat state {entity} {new}")
      door_open = self.get_state('input_boolean.dooropen')
      thermostat = self.get_state('climate.orem_property')
      fortress = self.get_state('input_boolean.secure')
      self.log(f"evaluate breach door {door_open} thermostat {thermostat} fortress {fortress}")
      self.commands['breach'] = True if door_open == 'on' else False
      if thermostat == 'off' and door_open == 'on':
          for light in self.smart_lights + self.dumb_lights:
              self.log(f"light change {light}")
              self.color_change(light, 2, self.temp_alert, command='breach')
      elif door_open == 'on':
          # fortress mode or regular door open-
          if fortress == 'on':
              for light in self.smart_lights + self.dumb_lights:
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
      self.log(f"Toggling {entity} {entity=='input_boolean.theater_lights'} lights {old} {new}")
      if entity=='input_boolean.theater_lights':
          command=f"theater-{new}"
          lights = self.theater_lights
          self.commands[f"theater-{new}"] = True
          self.commands[f"theater-{old}"] = False
          self.commands['dance'] = False
      elif entity=='input_boolean.kitchen_lights':
           command=f"kitchen-{new}"
           lights = self.kitchen_lights
           self.commands[f"kitchen-{new}"] = True
           self.commands[f"kitchen-{old}"] = False
           self.commands['dance'] = False
      elif entity=='input_boolean.patio_lights':
           command=f"patio-{new}"
           lights = self.patio_lights
           self.commands[f"patio-{new}"] = True
           self.commands[f"patio-{old}"] = False
           self.commands['dance'] = False
      elif entity=='input_boolean.fae_lights':
           command=f"fae-{new}"
           lights = self.fae_lights
           self.commands[f"fae-{new}"] = True
           self.commands[f"fae-{old}"] = False
           self.commands['dance'] = False
      elif entity=='input_boolean.ocean_lights':
           command=f"ocean-{new}"
           lights = self.ocean_lights
           self.commands[f"ocean-{new}"] = True
           self.commands[f"ocean-{old}"] = False
           self.commands['dance'] = False
      for light in lights:
        # self.log(f"command is {command} {self.commands[command]}")
        light_state = self.get_state(f"light.{light}", attribute='all')
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
        if hs_old is None:
            self.update_light(light, percent=0, total_duration=3, dur=.1,
                              color_temp=238, color_temp_old=color_temp_old,
                              brightness=255 if new=='on' else 0, brightness_old=brightness_old,
                              command=command)
        else:
            self.update_light(light, percent=0, total_duration=3, dur=.1,
                    color_temp=238,
                    brightness=255 if new=='on' else 0,
                    brightness_old=brightness_old, command=command)
            # self.run_in(lambda _: self.update_light(light, percent=0, total_duration=3/2, dur=.1,
            #         color_temp=238, brightness=255 if new=='on' else 0,
            #         brightness_old=self.get_state(f"light.{light}", attribute='brightness'),
            #         command=command), 1.6)
            # self.run_in(lambda _: self.update_light(light_id, percent=0, brightness=255), 1.6)
  def dance_start(self, entity,  attribute, old, new, kwargs):
      self.log("start dance")
      for command in self.commands:
          self.commands[command] = False
      self.commands['dance'] = True
      for name in self.dumb_lights:
        self.color_change_random(name, 30)
      for name in self.smart_lights:
        self.color_change_random(name, 30)
  def dance_stop(self, entity, attribute, old, new, kwargs):
      self.log('stop dance')
      self.commands['dance'] = False
  def wrap_hue(self, hue_old, hue_next):
    hue_diff = hue_next - hue_old
    if abs(hue_diff) > 180:
      if hue_next > hue_old:
        hue_diff = hue_diff % 360
      else:
        hue_diff = (hue_old - hue_next) - 360
    return hue_diff
  def update_light(self, light_id, **kwargs):
    if not self.commands[kwargs['command']]: return
    hass_kwargs = {'entity_id': f"light.{light_id}"}
    if light_id in self.smart_lights:
        if 'hs' in kwargs: hass_kwargs['hs_color'] = kwargs['hs']
        if 'rgb' in kwargs: hass_kwargs['rgb_color'] = kwargs['rgb']
        if 'color_temp' in kwargs: hass_kwargs['color_temp'] = kwargs['color_temp']
        if 'brightness' in kwargs: hass_kwargs['brightness'] = kwargs['brightness']
        if 'total_duration' in kwargs: hass_kwargs['transition'] = kwargs['total_duration']
        self.turn_on(**hass_kwargs)
        return

    if 'hs_old' in kwargs:
      percent = kwargs['percent']
      hass_kwargs['hs_color'] = [(kwargs['hs_old'][0] + self.wrap_hue(kwargs['hs_old'][0],kwargs['hs'][0])*percent)%360,
                                 kwargs['hs_old'][1] + (kwargs['hs'][1] - kwargs['hs_old'][1])*percent]
    elif 'hs' in kwargs: hass_kwargs['hs_color'] = kwargs['hs']
    if 'rgb_old' in kwargs:
      percent = kwargs['percent']
      hass_kwargs['rgb_color'] = [kwargs['rgb_old'][0] + (kwargs['rgb'][0] - kwargs['rgb_old'][0])*percent,
                                  kwargs['rgb_old'][1] + (kwargs['rgb'][1] - kwargs['rgb_old'][1])*percent,
                                  kwargs['rgb_old'][2] + (kwargs['rgb'][2] - kwargs['rgb_old'][2])*percent]
    elif 'rgb' in kwargs: hass_kwargs['rgb_color'] = kwargs['rgb']
    if 'color_temp_old' in kwargs:
      percent = kwargs['percent']
      hass_kwargs['color_temp'] = kwargs['color_temp_old'] + (kwargs['color_temp'] - kwargs['color_temp_old'])*percent
    elif 'color_temp' in kwargs: hass_kwargs['color_temp'] = kwargs['color_temp']
    if 'brightness_old' in kwargs:
        hass_kwargs['brightness'] = kwargs['brightness_old'] + (kwargs['brightness'] - kwargs['brightness_old'])*kwargs['percent']
    elif 'brightness' in kwargs: hass_kwargs['brightness'] = kwargs['brightness']

    if 'dur' in kwargs:
      hass_kwargs['transition'] = kwargs['dur']
      kwargs['percent'] += kwargs['dur']/kwargs['total_duration']
      if kwargs['percent'] < 1 + kwargs['dur']/kwargs['total_duration']:
        kwargs['percent'] = min(1,kwargs['percent'])
        self.run_in(lambda _: self.update_light(light_id, **kwargs), kwargs['dur'])
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

  def color_change_random(self, light_id, duration):
      if self.commands['dance']:
          light_state = self.get_state(f"light.{light_id}", attribute='all')
          if light_state['state']=='on':
              color_old = [light_state['attributes']['hs_color'][0],
                           light_state['attributes']['hs_color'][1],
                           light_state['attributes']['brightness']]
          else:
              color_old = [self.hsb[randint(0,len(self.hsb)-1)][0],
                           self.hsb[randint(0,len(self.hsb)-1)][1], 0]
          idx = randint(0,len(self.hsb)-1)
          color_next = self.hsb[idx]
          self.log(f"Next color {light_id} {color_old} -> {color_next}")
          self.update_light(light_id,
            hs_old=(color_old[0],color_old[1]), hs=(color_next[0],color_next[1]),
            brightness=color_next[2], brightness_old=color_old[2],
            percent=0, dur=self.step, total_duration=duration, command='dance')
          self.run_in(lambda _: self.color_change_random(light_id, duration), duration+self.step*4)

  # def color_change(self, light_id, duration, idx):
  #     if self.dance:
  #       self.log(f"Next color {light_id} {idx}")
  #       color_old = self.hsb[(idx - 1)%len(self.colors)]
  #       color_next = self.hsb[idx]
  #       self.update_light(light_id,
  #           hs_old=(color_old[0],color_old[1]), hs=(color_next[0],color_next[1]),
  #           brightness=color_next[2], brightness_old=color_old[2],
  #           percent=0, dur=self.step, total_duration=duration, dance=True)
  #       idx = (idx + 1) % len(self.hsb)
  #       self.run_in(lambda _: self.color_change(light_id, duration, idx), duration+self.step)
