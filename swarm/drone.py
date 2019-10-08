import time
import queue
import socket
import vizier.node
from dronekit import connect, VehicleMode
from pymavlink import mavutil

class Drone:
    def __init__(self, connection_string: str, host: str, port: int,
                 node_descriptor: dict,
                 vehicle_mode: str = "STABILIZE", verbose: bool = False):
        self._verbose = verbose
        self._event = {"armed": [], "connected":[], "disconnected":[], "disarmed": [], "message": []}
        self._initializeNode(host, port, node_descriptor)
        self._initializeVehicle(connection_string)
        self.setVehicleMode(vehicle_mode)
        self.started = False
    
    def start(self):
        self.started = True
        self._startNode()
        self._arm_vehicle()
        self._message_loop()
    
    def stop(self):
        if self.started:
            self.started = False
            self.node.stop()
            self._fire_event("disconnected")
            self._disarm_vehicle()
        elif self._verbose: print("Vehicle not started")
    
    def _message_loop(self):
        """
        Start listening and responding to MQTT commands
        """

        # Get the links for Publishing/Subscribing
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
        self.stop()
    
    
    def setVehicleMode(self, new_mode: str):
        if self._verbose: print("Switching mode from", self.vehicle.mode.name,
                                                    "to", new_mode)
        self.vehicle.mode = VehicleMode(new_mode)
        while self.vehicle.mode.name != new_mode:
            if self._verbose: print("Waiting for mode change...")
            time.sleep(1)
        if self._verbose: print("Successfully set mode ", self.vehicle.mode.name)

    def commandMavLink(self, gimbal: (int, int, int), speed: float):
        pitch, roll, yaw = gimbal
        if self._verbose: print("Pitch", pitch, ", roll", roll , ", yaw", yaw, ", speed", speed)
        self.vehicle.gimbal.rotate(pitch, roll, yaw)
        while (self.vehicle.gimbal.pitch, self.vehicle.gimbal.roll, self.vehicle.gimbal.yaw) != gimbal:
            if self._verbose: print("Current gimbal:", self.vehicle.gimbal)
        self.vehicle.airspeed = speed
        while self.vehicle.airspeed != speed:
            if self._verbose: print("current speed:", self.vehicle.airspeed)

    def addEventListener(self, event_name: str, listener: callable):
        self._event[event_name].append(listener)
    
    def removeEventListeners(self, event_name: str):
        self._event[event_name] = []
    
    def _fire_event(self, event_name: str, *args):
        for listener in self._event[event_name]:
            listener(*args)
                
    def _initializeNode(self, host: str, port: int, node_descriptor: object):
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

    def _initializeVehicle(self, connection_string: str):
        if self._verbose: print("Connecting to vehicle")
        connected = False
        while not connected:
            try:
                self.vehicle = connect(connection_string, wait_ready=True)
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