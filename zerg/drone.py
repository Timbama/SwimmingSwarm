import vizier.node
import time
import queue
from dronekit import connect, VehicleMode
from pymavlink import mavutil

class Drone:
    def __init__(self, connection_string: str, host: str, port: int,
                 node_descriptor: object,
                 vehicle_mode: str = "STABILIZE", verbose: bool = False):
        self._verbose = verbose
        self._event = {"armed": [], "connected":[], "disconnected":[], "disarmed": []}
        self._initializeNode(host, port, node_descriptor)
        self._initializeVehicle(connection_string)
        self.setVehicleMode(vehicle_mode)
        self.started = False
    
    def start(self):
        self.started = True
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
        if self._verbose: print("Starting Vizier")
        self.node.start()
        if self._verbose: print("Connected to Vizier")
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
                print(message)
                self._execute(message)
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
    
    def _execute(self, message: str):
        """
        Execute MQTT message
        """
        input = message[1:-1].split(',')
        yaw = float(input[0])
        throttle = float(input[1])
        pitch = float(input[2])
        depth = float(input[3])
        self._commandMavLink(vehicle, yaw, throttle, pitch, depth)

        
    def _initializeVehicle(self, connection_string: str):
        if self._verbose: print("Connecting to vehicle...")
        connected = False
        while not connected:
            try:
                self.vehicle = connect(connection_string, wait_ready=True)
                connected = True
            except Exception as e:
                if self._verbose:
                    print("Error:", e)
                    print("Retrying connection...")
            time.sleep(1)
    
    def setVehicleMode(self, new_mode: str):
        if self._verbose: print("Switching mode from", self.vehicle.mode.name,
                                                    "to", new_mode)
        self.vehicle.mode = VehicleMode(new_mode)
        while self.vehicle.mode.name != new_mode:
            if self._verbose: print("Waiting for mode change...")
            time.sleep(1)
        if self._verbose: print("Successfully set mode ", self.vehicle.mode.name)
    
    def _arm_vehicle(self):
        if self._verbose: print("Arming vehicle...")
        self.vehicle.armed = True
        while not self.vehicle.armed:
            if self._verbose: print("Waiting for arming...")
            time.sleep(1)
        self._fire_event("armed")
        if self._verbose: print("Vehicle armed")
    
    def _disarm_vehicle(self):
        if self._verbose: print("Disarming vehicle...")
        self.vehicle.armed = False
        while self.vehicle.armed:
            if self._verbose: print("Waiting for disarm")
            time.sleep(1)
        if self._verbose: print("Vehicle disarmed")
                
    def _initializeNode(self, host: str, port: int, node_descriptor: object):
        """
        Create a new Vizier connection Node
        """
        if self._verbose: print("Setting up Vizier node...")
        self.node = vizier.node.Node(host, port, node_descriptor)

    def _commandMavLink(self, yaw, throttle, pitch, depth):
        # Does nothing with the input yet
        # TODO: Pass actual commands to the vehicle
        # self.vehicle.channels.overrides = {}
        if self._verbose: print("Command", yaw, ",", throttle, ",", pitch, ",", depth)

    # Example velocity control code on Dronekit
    def send_ned_velocity(self, velocity_x, velocity_y, velocity_z, duration):
        """
        Move vehicle in direction based on specified velocity vectors.
        """
        msg = self.vehicle.message_factory.set_position_target_local_ned_encode(
            0,       # time_boot_ms (not used)
            0, 0,    # target system, target component
            mavutil.mavlink.MAV_FRAME_LOCAL_NED, # frame
            0b0000111111000111, # type_mask (only speeds enabled)
            0, 0, 0, # x, y, z positions (not used)
            velocity_x, velocity_y, velocity_z, # x, y, z velocity in m/s
            0, 0, 0, # x, y, z acceleration (not supported yet, ignored in GCS_Mavlink)
            0, 0)    # yaw, yaw_rate (not supported yet, ignored in GCS_Mavlink)

        # send command to vehicle on 1 Hz cycle
        for x in range(0,duration):
            self.vehicle.send_mavlink(msg)
            time.sleep(1)

    def addEventListener(self, event_name: str, listener: callable):
        self._event[event_name].append(listener)
    
    def removeEventListeners(self, event_name: str):
        self._event[event_name] = []
    
    def _fire_event(self, event_name: str, *args):
        for listener in self._event[event_name]:
            listener(*args)