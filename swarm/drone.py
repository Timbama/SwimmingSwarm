import json
import time
import queue
import socket
import vizier.node
from dronekit import connect, VehicleMode, LocationGlobal

from swarm.gps import MockGPS

class Drone:
    def __init__(self, connection_string: str, host: str, port: int,
                 node_descriptor: dict, vehicle_mode: str,
                 local: bool = False, verbose: bool = False):
        self._verbose = verbose
        self._local = local
        self._event = {
            "armed": [], "connected":[], "disconnected":[],
            "disarmed": [], "message": [], "loop": []
            }
        if not local:
            if self._verbose: print("Setting up Vizier node...")
            self.node = vizier.node.Node(host, port, node_descriptor)
        self._init_vehicle(connection_string)
        guided_parameters = {
            "EK3_ENABLE": 1,
            "EK2_ENABLE": 0,
            "AHRS_EKF_TYPE": 3,
            "EK3_GPS_TYPE": 0,
            "EK3_MAG_CAL": 5,
            "EK3_ALT_SOURCE": 2,
            "GPS_TYPE": 14,
            "GPS_DELAY_MS": 50,
            "COMPASS_USE": 0,
            "COMPASS_USE2": 0,
            "COMPASS_USE3": 0
        }
        if vehicle_mode == "GUIDED":
            for key in guided_parameters:
                self.vehicle.parameters[key] = guided_parameters[key]
        if self._verbose: print("Parameters", self.vehicle.parameters)
        self._vehicle_mode = vehicle_mode
        self.started = False

        # TODO: Add actual GPS
        self.gps = MockGPS(0, 0)
    
    def start(self):
        self.started = True
        self.set_vehicle_mode(self._vehicle_mode)
        self._arm_vehicle()
        self._message_loop()
    
    def stop(self):
        if self.started:
            self.started = False
            if not self._local:
                self.node.stop()
                self._fire_event("disconnected")
            self._disarm_vehicle()
        elif self._verbose: print("Vehicle not started")
    
    def _message_loop(self):
        """
        Start listening and responding to MQTT commands
        """
        if not self._local:
            self._start_node()
            publishable_link = list(self.node.publishable_links)[0]
            subscribable_link = list(self.node.subscribable_links)[0]
            msg_queue = self.node.subscribe(subscribable_link)
            self._fire_event("connected")
            if self._verbose: print("Subscribed to broker")
        
            state = {"alive": True}
            if self.vehicle.mode.name == "GUIDED": state["gps"] = self.gps.encoded_coord()

            # Send the initial condition to the PC
            self.node.publish(publishable_link, json.dumps(state, separators = (',', ':')))
            if self._verbose: print("Sent initial state")
            while state["alive"] == True:
                try:
                    # Receive and decode the message
                    message = msg_queue.get(timeout=0.1).decode(encoding = 'UTF-8')
                    if self._verbose: print(message)
                    # Fire any commands
                    self._fire_event("message", self, message)
                except queue.Empty:
                    # Just pass if the queue is empty (no message received yet)
                    pass
                except KeyboardInterrupt:
                    # Stop when there's keyboard interrupt on the PI
                    state["alive"] =  False
                except Exception as e:
                    if self._verbose: print(e)
                    # Stop when there's other exception
                    state["alive"] =  False
                finally:

                    if self.vehicle.mode.name == "GUIDED":
                        # TODO: Remove for actual GPS. Step the mock gps simlation.
                        self.gps.step(0.01)
                        # Update the state
                        state["gps"] = self.gps.encoded_coord()
                        # Send updated GPS
                        self.send_GPS(self.gps.lat, self.gps.lon, alt=0)

                    self._fire_event("loop", self)
                    # Always send the updated state to the PC
                    self.node.publish(publishable_link, json.dumps(state, separators = (',', ':')))
        else:
            state = 1
            while state == 1:
                try:
                    self._fire_event("message", self, "")
                except KeyboardInterrupt:
                    # Stop when there's keyboard interrupt on the PI
                    state = 0
                except Exception as e:
                    if self._verbose: print(e)
                    state = 0

        self.stop()

    def set_vehicle_mode(self, new_mode: str):
        if self._verbose: print("Switching mode from", self.vehicle.mode.name, "to", new_mode)
        self.vehicle.mode = VehicleMode(new_mode)
        while self.vehicle.mode.name != new_mode:
            if self._verbose: print("Waiting for mode change...")
            if new_mode == "GUIDED":
                self.send_GPS(self.gps.lat, self.gps.lon, alt=0)
            time.sleep(1)
        if self._verbose: print("Successfully set mode ", self.vehicle.mode.name)

    def add_event_listener(self, event_name: str, listener: callable):
        self._event[event_name].append(listener)
 
    def remove_event_listeners(self, event_name: str):
        self._event[event_name] = []
    
    def _fire_event(self, event_name: str, *args):
        for listener in self._event[event_name]:
            listener(*args)
                
    def _start_node(self):
        if self._verbose: print("Starting Vizier")
        connected = False
        while not connected:
            try:
                # Probing broker
                prober = socket.create_connection((self.node._host, self.node._port))
                connected = True
                prober.close()
            except Exception as e:
                print("Retrying:", e)
                time.sleep(1)
        self.node.start()
        if self._verbose: print("Connected to Vizier")

    def _init_vehicle(self, connection_string: str):
        if self._verbose: print("Connecting to vehicle")
        connected = False
        while not connected:
            try:
                self.vehicle = connect(connection_string, wait_ready=True)
                self.vehicle.wait_ready(True)
                connected = True
            except Exception as e:
                if self._verbose:
                    print("Retrying:", e)
            time.sleep(1)

    def _arm_vehicle(self):
        if self._verbose: print("Arming vehicle")
        self.vehicle.armed = True
        while not self.vehicle.armed:
            if self._verbose: print("Waiting for arming...")
            time.sleep(1)
        self._fire_event("armed")
        if self._verbose: print("Vehicle armed")
    
    def _disarm_vehicle(self):
        if self._verbose: print("Disarming vehicle")
        self.vehicle.armed = False
        while self.vehicle.armed:
            if self._verbose: print("Waiting for disarm...")
            self.vehicle.armed = False
            time.sleep(1)
        if self._verbose: print("Vehicle disarmed")

    def channel_command(self, pitch: int, roll: int, yaw: int, throttle: int):
        if self._verbose: print(roll, pitch, throttle, yaw)
        # Ch1 =Roll, Ch 2=Pitch, Ch 3=Horizontal throttle, Ch 4=Yaw, Ch 5=Forward throttle
        self.vehicle.channels.overrides['1'] = roll
        self.vehicle.channels.overrides['2'] = pitch
        self.vehicle.channels.overrides['5'] = throttle
        self.vehicle.channels.overrides['4'] = yaw

    def guided_command(self, lat: float, lon: float, alt = 0):
        if self._verbose: print(lat, lon, alt)
        self.vehicle.simple_goto(LocationGlobal(lat, lon, alt))
    
    def send_GPS(self, lat: float, lon: float, alt: float, satellites_visible = 3):
        gps_fix_type = {
            "no_fix": 0, "2d_fix": 2,
            "3d_fix": 3, "dgps": 4, "rtk_float": 5
        }
        ignore = {
            "alt": 1, "hdop": 2, "vdop": 4, "vel_horiz": 8, "vel_vert": 16,
            "speed_accuracy": 32, "horizontal_accuracy": 64, "vertical_accuracy": 128
        }
        ignore_flags = ignore["vel_horiz"] | ignore["vel_vert"]
        ignore_flags = ignore_flags | ignore["speed_accuracy"] | ignore["horizontal_accuracy"]
        msg = self.vehicle.message_factory.gps_input_encode(
            int(time.time()*10000), #Timestamp (micros since boot or Unix epoch)
            0,                      #ID of the GPS for multiple GPS inputs
            ignore,                 #Flags indicating which fields to ignore (see GPS_INPUT_IGNORE_FLAGS enum). All other fields must be provided.
            0,                      #GPS time (milliseconds from start of GPS week)
            0,                      #GPS week number
            gps_fix_type["3d_fix"], #0-1: no fix, 2: 2D fix, 3: 3D fix. 4: 3D with DGPS. 5: 3D with RTK
            int(lat * (10**7)),     #Latitude (WGS84), in degrees * 1E7
            int(lon * (10**7)),     #Longitude (WGS84), in degrees * 1E7
            alt,                    #Altitude (AMSL, not WGS84), in m (positive for up)
            0,                      #GPS HDOP horizontal dilution of position in m
            0,                      #GPS VDOP vertical dilution of position in m
            0,                      #GPS velocity in m/s in NORTH direction in earth-fixed NED frame
            0,                      #GPS velocity in m/s in EAST direction in earth-fixed NED frame
            0,                      #GPS velocity in m/s in DOWN direction in earth-fixed NED frame
            0,                      #GPS speed accuracy in m/s
            0,                      #GPS horizontal accuracy in m
            0,                      #GPS vertical accuracy in m
            satellites_visible      #Number of satellites visible.
        )
        self.vehicle.send_mavlink(msg)
