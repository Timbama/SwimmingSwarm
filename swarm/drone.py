import time
import queue
import socket
import vizier.node
from dronekit import connect, VehicleMode

class Drone:
    def __init__(self, connection_string: str, host: str, port: int,
                 node_descriptor: dict, vehicle_mode: str = "STABILIZE",
                 local: bool = False, verbose: bool = False):
        self._verbose = verbose
        self._local = local
        self._event = {"armed": [], "connected":[], "disconnected":[], "disarmed": [], "message": []}
        if not local:
            self._initNode(host, port, node_descriptor)
        self._initVehicle(connection_string)
        self.setVehicleMode(vehicle_mode)
        self._initCommands()
        self.started = False
    
    def start(self):
        self.started = True
        if not self._local:
            self._startNode()
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

            # Set the initial condition
            # 1 is good, 0 is stop
            state = 1

            # Send the initial condition to the PC
            self.node.publish(publishable_link, str(state))
            while state == 1:
                try:
                    # Receive and decode the message
                    message = msg_queue.get(timeout=0.1).decode(encoding = 'UTF-8')
                    self._fire_event("message", self, message)
                except KeyboardInterrupt:
                    # Stop when there's keyboard interrupt on the PI
                    state = 0
                except queue.Empty:
                    # Just continue if the queue is empty
                    continue
                except Exception as e:
                    if self._verbose: print(e)
                    # Stop when there's other exception
                    state = 0
                finally:
                    # Always send the updated condition to the PC
                    self.node.publish(publishable_link, str(state))
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

    def setVehicleMode(self, new_mode: str):
        if self._verbose: print("Switching mode from", self.vehicle.mode.name,
                                                    "to", new_mode)
        self.vehicle.mode = VehicleMode(new_mode)
        while self.vehicle.mode.name != new_mode:
            if self._verbose: print("Waiting for mode change...")
            time.sleep(1)
        if self._verbose: print("Successfully set mode ", self.vehicle.mode.name)

    def addEventListener(self, event_name: str, listener: callable):
        self._event[event_name].append(listener)
 
    def removeEventListeners(self, event_name: str):
        self._event[event_name] = []
    
    def _fire_event(self, event_name: str, *args):
        for listener in self._event[event_name]:
            listener(*args)
                
    def _initNode(self, host: str, port: int, node_descriptor: object):
        """
        Create a new Vizier connection Node
        """
        if self._verbose: print("Setting up Vizier node...")
        self.node = vizier.node.Node(host, port, node_descriptor)
    
    def _startNode(self):
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

    def _initVehicle(self, connection_string: str):
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

    def channelCommand(self, pitch: float, roll: float, yaw: float, throttle: float):
        # Ch1 =Roll, Ch 2=Pitch, Ch 3=Throttle, Ch 4=Yaw
        self.vehicle.channels.overrides[0] = roll
        self.vehicle.channels.overrides[1] = pitch
        self.vehicle.channels.overrides[2] = throttle
        self.vehicle.channels.overrides[3] = yaw

    def stabilizedCommand(self, pitch: float, roll: float, yaw: float, speed: float):
        self.vehicle.gimbal.rotate(pitch, roll, yaw)
        self.vehicle.airspeed = speed
    
    def sendGPS(self, lat, lon, alt, eph = 65535, epv = 65535, vel = 65535, cog = 65535, satellites_visible = 255,
        alt_ellipsoid = None, h_acc = None, v_acc = None, vel_acc = None, hdg_acc = None):
        gps_fix_type = {
            "no_gps": 0, "no_fix": 1, "2d_fix": 2, "3d_fix": 3,
            "dgps": 4, "rtk_float": 5, "rtk_fixed": 6, "static": 7, "ppp": 8
            }
        msg = None
        if (alt_ellipsoid == None and h_acc == None and v_acc == None and vel_acc == None and hdg_acc == None):
            msg = self.vehicle.message_factory.gps_raw_int_encode(
                int(time.time()),
                gps_fix_type["2d_fix"],
                lat, lon, alt, eph, epv, vel, cog, satellites_visible
            )
            vehicle.send_mavlink(msg)
        else:
            msg = self.vehicle.message_factory.gps_raw_int_encode(
                int(time.time()),
                gps_fix_type["2d_fix"],
                lat, lon, alt, eph, epv, vel, cog, satellites_visible,
                alt_ellipsoid, h_acc, v_acc, vel_acc, hdg_acc
            )
            vehicle.send_mavlink(msg)
