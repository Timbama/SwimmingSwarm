import vizier.node
import time
import queue
from dronekit import connect, VehicleMode
from pymavlink import mavutil

class SwarmBot:
    def __init__(self, connection_string: str, host: str, port: int,
                 node_descriptor: object,
                 vehicle_mode: str = "STABILIZE", verbose: bool = False):
        self.__verbose__ = verbose
        self.__event__ = {"armed": [], "disarmed": [], "connected": [], "disconnected": []}
        self.__initializeNode__(host, port, node_descriptor)
        self.__initializeVehicle__(connection_string)
        self.setVehicleMode(vehicle_mode)
        self.started = False
    
    def start(self):
        self.started = True
        self.__arm_vehicle__()
        self.__message_loop__()
    
    def stop(self):
        if self.started:
            self.started = False
            self.node.stop()
            self.__fire_event__("disconnected")
            self.__disarm_vehicle__()
        elif self.__verbose__: print("Vehicle not started")

    def __message_loop__(self):
        """
        Start listening and responding to MQTT commands
        """
        self.node.start()
        # Get the links for Publishing/Subscribing
        publishable_link = list(self.node.publishable_links)[0]
        subscribable_link = list(self.node.subscribable_links)[0]
        msg_queue = self.node.subscribe(subscribable_link)
        self.__fire_event__("connected")

        # Set the initial condition
        # 1 is good, 0 is stop
        state = 1

        # Send the initial condition to the PC
        self.node.publish(publishable_link, str(state))
        while state == 1:
            try:
                # Receive and decode the message
                message = msg_queue.get(timeout=0.1).decode(encoding = 'UTF-8')
                self.__execute__(message)
            except KeyboardInterrupt:
                # Stop when there's keyboard interrupt on the PI
                state = 0
            except queue.Empty:
                # Just continue if the queue is empty
                continue
            except Exception as e:
                if self.__verbose__: print(e)
                # Stop when there's other exception
                state = 0
            
            # Send the updated initial condition to the PC
            self.node.publish(publishable_link, str(state))
        self.stop()
    
    def __execute__(self, message: str):
        """
        Execute MQTT message
        """
        input = message[1:-1].split(',')
        yaw = float(input[0])
        throttle = float(input[1])
        pitch = float(input[2])
        depth = float(input[3])
        self.__commandMavLink__(vehicle, yaw, throttle, pitch, depth)

        
    def __initializeVehicle__(self, connection_string: str):
        if self.__verbose__: print("Connecting to vehicle...")
        connected = False
        while not connected:
            try:
                self.vehicle = connect(connection_string, wait_ready=True)
                connected = True
            except Exception as e:
                if self.__verbose__:
                    print("Error:", e)
                    print("Retrying connection...")
            time.sleep(1)
    
    def setVehicleMode(self, new_mode: str):
        if self.__verbose__: print("Switching mode from", self.vehicle.mode.name,
                                                    "to", new_mode)
        self.vehicle.mode = VehicleMode(new_mode)
        while self.vehicle.mode.name != new_mode:
            if self.__verbose__: print("Waiting for mode change...")
            time.sleep(1)
        if self.__verbose__: print("Successfully set mode ", self.vehicle.mode.name)
    
    def __arm_vehicle__(self):
        if self.__verbose__: print("Arming vehicle...")
        self.vehicle.armed = True
        while not self.vehicle.armed:
            if self.__verbose__: print("Waiting for arming...")
            time.sleep(1)
        self.__fire_event__("armed")
        if self.__verbose__: print("Vehicle armed")
    
    def __disarm_vehicle__(self):
        if self.__verbose__: print("Disarming vehicle...")
        self.vehicle.armed = False
        while self.vehicle.armed:
            if self.__verbose__: print("Waiting for disarm")
            time.sleep(1)
        if self.__verbose__: print("Vehicle disarmed")
                
    def __initializeNode__(self, host: str, port: int, node_descriptor):
        """
        Create a new Vizier connection Node
        """
        if self.__verbose__: print("Setting up Vizier node...")
        self.node = vizier.node.Node(host, port, node_descriptor)

    def __commandMavLink__(self, yaw, throttle, pitch, depth):
        # Does nothing with the input yet
        # TODO: Pass actual commands to the vehicle
        # self.vehicle.channels.overrides = {}
        if self.__verbose__: print("Command", yaw, ",", throttle, ",", pitch, ",", depth)

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
        # All events are expected to expect one return argument:
        # the Swarmbot object itself
        self.__event__[event_name].append(listener)
    
    def removeEventListeners(self, event_name: str):
        self.__event__[event_name] = []
    
    def __fire_event__(self, event_name: str):
        # All events are expected to expect one return argument:
        # the Swarmbot object itself
        for listener in self.__event__[event_name]:
            listener(self)