import json
import time
import queue
import socket
import vizier.node
from dronekit import connect, VehicleMode, LocationGlobal

from swarm.gps import MockGPS

class Drone:
    def __init__(self, connection_string: str, host: str, port: int,
                 node_descriptor: dict, vehicle_mode = None,
                 local: bool = False, verbose: bool = False):
        self._verbose = verbose
        self._local = local
        self._event = {
            "armed": [], "connected":[], "disconnected":[],
            "disarmed": [], "message": [], "loop": []
            }
        if not local:
            self._init_node(host, port, node_descriptor)
        if local and vehicle_mode != None:
            self.set_vehicle_mode(vehicle_mode)
        self._init_vehicle(connection_string)
        self.started = False

        # TODO: Add actual GPS
        self.gps = MockGPS(0, 0)
    
    def start(self):
        self.started = True
        if not self._local:
            self._start_node()
        subscribable_link = list(self.node.subscribable_links)[0]
        msg_queue = self.node.subscribe(subscribable_link)
        received_setup_config = False
        vehicle_mode = None
        while not received_setup_config:
            setup_message = msg_queue.get().decode(encoding = 'UTF-8')
            setup_config = json.loads(setup_message)
            if "vehicle_mode" in setup_config:
                vehicle_mode = setup_config["vehicle_mode"]
                received_setup_config = True
            if "start_time" in setup_config:
                self.start_time = setup_config["start_time"]
            if "parameters" in setup_config:
                for key in setup_config["parameters"]:
                    self.vehicle.parameters[key] = setup_config["parameters"][key]
            time.sleep(0.5)
        self.set_vehicle_mode(vehicle_mode)
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
            publishable_link = list(self.node.publishable_links)[0]
            subscribable_link = list(self.node.subscribable_links)[0]
            msg_queue = self.node.subscribe(subscribable_link)
            self._fire_event("connected")
        
            state = {"alive": True, "time_shift": time.time() - self.start_time, "gps": self.gps.encoded_coord()}

            # Send the initial condition to the PC
            self.node.publish(publishable_link, json.dumps(state, separators = (',', ':')))
            while state["alive"] == True:
                try:
                    # Receive and decode the message
                    message = msg_queue.get(timeout=0.1).decode(encoding = 'UTF-8')

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
                    # TODO: Remove for actual GPS. Step the mock gps simlation.
                    self.gps.step(0.01)

                    # Update the state
                    state["time_shift"] = time.time() - self.start_time
                    state["gps"] = self.gps.encoded_coord()
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
            time.sleep(1)
        if self._verbose: print("Successfully set mode ", self.vehicle.mode.name)

    def add_event_listener(self, event_name: str, listener: callable):
        self._event[event_name].append(listener)
 
    def remove_event_listeners(self, event_name: str):
        self._event[event_name] = []
    
    def _fire_event(self, event_name: str, *args):
        for listener in self._event[event_name]:
            listener(*args)
                
    def _init_node(self, host: str, port: int, node_descriptor: object):
        """
        Create a new Vizier connection Node
        """
        if self._verbose: print("Setting up Vizier node...")
        self.node = vizier.node.Node(host, port, node_descriptor)
    
    def _start_node(self):
        if self._verbose: print("Starting Vizier")
        connected = False
        while not connected:
            try:
                # Probing broker
                prober = socket.create_connection((self.node._host, self.node._port))
                self.node.start()
                connected = True
                prober.close()
            except Exception as e:
                print("Retrying:", e)
                time.sleep(1)
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
            time.sleep(1)
        if self._verbose: print("Vehicle disarmed")

    def channel_command(self, pitch: float, roll: float, yaw: float, throttle: float):
        def pwm(value):
            center = (1300 + 1700)/2
            diff = (1700 - 1300)/2
            return int(center + (diff * value))

        # Ch1 =Roll, Ch 2=Pitch, Ch 3=Throttle, Ch 4=Yaw
        self.vehicle.channels.overrides[0] = pwm(roll)
        self.vehicle.channels.overrides[1] = pwm(pitch)
        self.vehicle.channels.overrides[2] = pwm(throttle)
        self.vehicle.channels.overrides[3] = pwm(yaw)

    def stabilized_command(self, pitch: float, roll: float, yaw: float, speed: float):
        self.vehicle.gimbal.rotate(pitch, roll, yaw)
        self.vehicle.airspeed = speed
    
    def guided_command(self, lat: float, lon: float, alt = 0):
        self.vehicle.simple_goto(LocationGlobal(lat, lon, alt))
    
    def send_GPS(self, lat: float, lon: float, alt: float, satellites_visible = 2):
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
            time.time(),            #Timestamp (micros since boot or Unix epoch)
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
