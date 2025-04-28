# Copyright 2025 Thomas Dalla Piazza.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


import asyncio
from asyncua import Server, ua
from asyncua.common.methods import uamethod

import rclpy
from rclpy.node import Node
from rclpy.task import Future

from printer_interfaces.msg import PrinterState, HeaterBed, Extruder, Fans, PrintStats
from printer_interfaces.srv import GetPrinterInfo, QueryEndStops, SetBedTemperature, SetExtruderTemperature, StartPrintJob, ExecuteGCode

class OpcuaBridge(Node):

    def __init__(self):
        super().__init__('opcua_bridge')

        # setup our opc server
        self.server = Server()
        self.endpoint='opc.tcp://0.0.0.0:4840/freeopcua/server/'
        self.uri='http://automation.ceff.ch'

        self.printerObj = None

        # Setup subscriptions
        self.setup_subscriptions()

        # Setup services clients
        self.setup_clients()

        

    def setup_subscriptions(self):
        self.printer_state_sub_ = self.create_subscription(
            PrinterState,
            'moonraker_bridge/status/state',
            self.update_printer_state,
            10
        )
        self.heater_bed_sub_ = self.create_subscription(
            HeaterBed,
            'moonraker_bridge/status/heater_bed',
            self.update_heater_bed,
            10
        )
        self.extruder_sub_ = self.create_subscription(
            Extruder,
            'moonraker_bridge/status/extruder',
            self.update_extruder,
            10
        )
        self.fans_sub_ = self.create_subscription(
            Fans,
            'moonraker_bridge/status/fans',
            self.update_fans,
            10
        )
        self.print_stats_sub_ = self.create_subscription(
            PrintStats,
            'moonraker_bridge/status/print_stats',
            self.update_print_stats,
            10
        )

    def setup_clients(self):
        # wait for service to be available
        self.get_printer_info_client_ = self.create_client(GetPrinterInfo, 'moonraker_bridge/commands/get_printer_info')
        self.query_end_stops_client_ = self.create_client(QueryEndStops, 'moonraker_bridge/commands/query_endstops')
        self.set_bed_temperature_client_ = self.create_client(SetBedTemperature, 'moonraker_bridge/commands/set_bed_temperature')
        self.set_extruder_temperature_client_ = self.create_client(SetExtruderTemperature, 'moonraker_bridge/commands/set_extruder_temperature')
        self.start_print_job_client_ = self.create_client(StartPrintJob, 'moonraker_bridge/commands/start_print_job')
        self.execute_gcode_client_ = self.create_client(ExecuteGCode, 'moonraker_bridge/commands/execute_gcode')
        while not self.get_printer_info_client_.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('service not available, waiting again...')
        while not self.query_end_stops_client_.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('service not available, waiting again...')
        while not self.set_bed_temperature_client_.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('service not available, waiting again...')
        while not self.set_extruder_temperature_client_.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('service not available, waiting again...')
        while not self.start_print_job_client_.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('service not available, waiting again...')
        while not self.execute_gcode_client_.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('service not available, waiting again...')


    async def process_printer_info_msg(self, future: Future):
        response=future.result()
        if response is not None:
            a_node = await self.printerObj.get_child([f"{self.idx}:Info", f"{self.idx}:Name"])
            await a_node.set_value(response.hostname)
            a_node = await self.printerObj.get_child([f"{self.idx}:Info", f"{self.idx}:Manufacturer"])
            await a_node.set_value(response.manufacturer)
            a_node = await self.printerObj.get_child([f"{self.idx}:Info", f"{self.idx}:Model"])
            await a_node.set_value(response.model)
            a_node = await self.printerObj.get_child([f"{self.idx}:Info", f"{self.idx}:Location"])
            await a_node.set_value(response.location)
            a_node = await self.printerObj.get_child([f"{self.idx}:Info", f"{self.idx}:CPU info"])
            await a_node.set_value(response.cpu_info)
            a_node = await self.printerObj.get_child([f"{self.idx}:Info", f"{self.idx}:State"])
            await a_node.set_value(response.state)
            a_node = await self.printerObj.get_child([f"{self.idx}:Systems", f'{self.idx}:Bed', f"{self.idx}:X dimension"])
            await a_node.set_value(response.bed_x_dimension)
            a_node = await self.printerObj.get_child([f"{self.idx}:Systems", f'{self.idx}:Bed', f"{self.idx}:Y dimension"])
            await a_node.set_value(response.bed_y_dimension)
            a_node = await self.printerObj.get_child([f"{self.idx}:Systems", f'{self.idx}:Bed', f"{self.idx}:Rated power"])
            await a_node.set_value(response.bed_rated_power)
            a_node = await self.printerObj.get_child([f"{self.idx}:Systems", f'{self.idx}:Hotend', f"{self.idx}:Manufacturer"])
            await a_node.set_value(response.hotend_manufacturer)
            a_node = await self.printerObj.get_child([f"{self.idx}:Systems", f'{self.idx}:Hotend', f"{self.idx}:Model"])
            await a_node.set_value(response.hotend_model)
            a_node = await self.printerObj.get_child([f"{self.idx}:Systems", f'{self.idx}:Hotend', f"{self.idx}:Rated power"])
            await a_node.set_value(response.hotend_rated_power)
            a_node = await self.printerObj.get_child([f"{self.idx}:Systems", f'{self.idx}:Hotend', f"{self.idx}:Nozzle diameter"])
            await a_node.set_value(response.hotend_nozzle_diameter)
        else:
            self.get_logger().warning('The printer_info response is empty...')

    
    async def update_printer_state(self, msg):
        if self.printerObj is not None:
            if msg.previous_state == PrinterState.NOT_READY and msg.current_state == PrinterState.READY:
                future = self.get_printer_info_client_.call_async(GetPrinterInfo.Request())
                future.add_done_callback(self.process_printer_info_msg)
            
            a_node = await self.printerObj.get_child([f"{self.idx}:Info", f"{self.idx}:State"])
            await a_node.set_value(msg.current_state)
            self.get_logger().info('Setting state value to: "%s"' % msg.current_state)
        else:
            self.get_logger().warning('Processing printer_state message but address_space not currently setup')

    async def update_heater_bed(self, msg):
        if self.printerObj is not None:
            a_node = await self.printerObj.get_child([f'{self.idx}:Systems', f'{self.idx}:Bed', f'{self.idx}:Temperature'])
            await a_node.set_value(msg.temperature)
            a_node = await self.printerObj.get_child([f'{self.idx}:Systems', f'{self.idx}:Bed', f'{self.idx}:Temperature set point'])
            await a_node.set_value(msg.target)
            a_node = await self.printerObj.get_child([f'{self.idx}:Systems', f'{self.idx}:Bed', f'{self.idx}:Power (PWM)'])
            await a_node.set_value(msg.power_pwm)

        else:
            self.get_logger().warning('Processing heater_bed message but address_space not currently setup')
    
    async def update_extruder(self, msg):
        if self.printerObj is not None:
            a_node = await self.printerObj.get_child([f'{self.idx}:Systems', f'{self.idx}:Hotend', f'{self.idx}:Temperature'])
            await a_node.set_value(msg.temperature)
            a_node = await self.printerObj.get_child([f'{self.idx}:Systems', f'{self.idx}:Hotend', f'{self.idx}:Temperature set point'])
            await a_node.set_value(msg.target)
            a_node = await self.printerObj.get_child([f'{self.idx}:Systems', f'{self.idx}:Hotend', f'{self.idx}:Power (PWM)'])
            await a_node.set_value(msg.power_pwm)

        else:
            self.get_logger().warning('Processing heater_bed message but address_space not currently setup')
        
    async def update_fans(self, msg):
        if self.printerObj is not None:
            a_node = await self.printerObj.get_child([f'{self.idx}:Systems', f'{self.idx}:Frame', f'{self.idx}:Controller fan ON'])
            await a_node.set_value(False if msg.controller_fan_speed == 0.0 else True)
            a_node = await self.printerObj.get_child([f'{self.idx}:Systems', f'{self.idx}:Hotend', f'{self.idx}:Hot end fan ON'])
            await a_node.set_value(False if msg.heater_fan_speed == 0.0 else True)
            a_node = await self.printerObj.get_child([f'{self.idx}:Systems', f'{self.idx}:Hotend', f'{self.idx}:Piece cooling fan speed'])
            await a_node.set_value(msg.piece_cooling_fan_speed)

        else:
            self.get_logger().warning('Processing heater_bed message but address_space not currently setup')

    async def update_print_stats(self, msg):
        if self.printerObj is not None:
            a_node = await self.printerObj.get_child([f'{self.idx}:Job', f'{self.idx}:State'])
            await a_node.set_value(msg.state)
            a_node = await self.printerObj.get_child([f'{self.idx}:Job', f'{self.idx}:Filename'])
            await a_node.set_value(msg.filename)
            a_node = await self.printerObj.get_child([f'{self.idx}:Job', f'{self.idx}:Total job duration [s]'])
            await a_node.set_value(msg.total_duration)
            a_node = await self.printerObj.get_child([f'{self.idx}:Job', f'{self.idx}:Job print time spent [s]'])
            await a_node.set_value(msg.print_duration)


        else:
            self.get_logger().warning('Processing heater_bed message but address_space not currently setup')

    @uamethod
    async def query_endstops(self, parent):
        future = self.query_end_stops_client_.call_async(QueryEndStops.Request())
        await asyncio.ensure_future(future)
        response=future.result()
        x = True if response.x == 'TRIGGERED' else False
        y = True if response.y == 'TRIGGERED' else False
        z = True if response.z == 'TRIGGERED' else False
        return x, y, z
    
    @uamethod
    async def set_bed_temperature(self, parent, temp):
        req = SetBedTemperature.Request()
        req.temperature = temp
        future = self.set_bed_temperature_client_.call_async(req)
        await asyncio.ensure_future(future)
        return future.result().result

    
    @uamethod
    async def set_extruder_temperature(self, parent, temp):
        req = SetExtruderTemperature.Request()
        req.temperature = temp
        future = self.set_extruder_temperature_client_.call_async(req)
        await asyncio.ensure_future(future)
        return future.result().result

    @uamethod
    async def start_printing(self, parent, file):
        req = StartPrintJob.Request()
        req.filename = file
        future = self.start_print_job_client_.call_async(req)
        await asyncio.ensure_future(future)
        return future.result().result

    @uamethod
    async def home_all_axes(self, parent):
        req = ExecuteGCode.Request()
        req.script = 'G28'
        future = self.execute_gcode_client_.call_async(req)
        await asyncio.ensure_future(future)
        return future.result().result

    
    async def setup_address_space(self):
        # Init the opc server
        await self.server.init()
        self.server.set_endpoint(self.endpoint)
        self.server.set_server_name("Voron0 printer OPC UA server")
        # set all possible endpoint policies for clients to connect through
        self.server.set_security_policy(
            [
                ua.SecurityPolicyType.NoSecurity,
                ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt,
                ua.SecurityPolicyType.Basic256Sha256_Sign,
            ]
        )

        # set up our own namespace, not really necessary but should as spec
        self.idx = await self.server.register_namespace(self.uri)
        # populating our address space
        # server.nodes, contains links to very common nodes like objects and root

        # printer object
        dev = await self.server.nodes.base_object_type.add_object_type(self.idx, '3D printer type')
        self.printerObj = await self.server.nodes.objects.add_object(self.idx, '3D printer', dev)
        #   info object
        printerInfoObj = await self.printerObj.add_object(self.idx, "Info")
        await printerInfoObj.add_property(self.idx, "Name", ua.Variant('', ua.VariantType.String))
        await printerInfoObj.add_property(self.idx, "Manufacturer", ua.Variant('', ua.VariantType.String))
        await printerInfoObj.add_property(self.idx, "Model", ua.Variant('', ua.VariantType.String))
        await printerInfoObj.add_property(self.idx, "Location", ua.Variant('', ua.VariantType.String))
        await printerInfoObj.add_property(self.idx, "CPU info", ua.Variant('', ua.VariantType.String))
        await printerInfoObj.add_variable(self.idx, "State", ua.Variant('', ua.VariantType.String))

        #   systems object
        printerSystemObj = await self.printerObj.add_object(self.idx, "Systems")
        #      bed
        printerBedObj = await printerSystemObj.add_object(self.idx, "Bed")
        await printerBedObj.add_property(self.idx, "X dimension", 0.0)
        await printerBedObj.add_property(self.idx, "Y dimension", 0.0)
        await printerBedObj.add_property(self.idx, "Rated power", 0.0)
        await printerBedObj.add_variable(self.idx, "Temperature", 0.0)
        await printerBedObj.add_variable(self.idx, "Temperature set point", 0.0)
        await printerBedObj.add_variable(self.idx, "Power (PWM)", 0.0)
        await printerBedObj.add_variable(self.idx, "Print plate present", ua.Variant(False, ua.VariantType.Boolean))
        await printerBedObj.add_variable(self.idx, "Print plate ID", 0)

        #      hotend
        printerHotendObj = await printerSystemObj.add_object(self.idx, "Hotend")
        await printerHotendObj.add_property(self.idx, "Manufacturer", ua.Variant('', ua.VariantType.String))
        await printerHotendObj.add_property(self.idx, "Model", ua.Variant('', ua.VariantType.String))
        await printerHotendObj.add_property(self.idx, "Rated power", 0.0)
        await printerHotendObj.add_property(self.idx, "Nozzle diameter", 0.0)
        await printerHotendObj.add_variable(self.idx, "Nozzle printing hours", 0.0)
        await printerHotendObj.add_variable(self.idx, "Umblilical printing hours", 0.0)
        await printerHotendObj.add_variable(self.idx, "Temperature", 0.0)
        await printerHotendObj.add_variable(self.idx, "Temperature set point", 0.0)
        await printerHotendObj.add_variable(self.idx, "Power (PWM)", 0.0)
        await printerHotendObj.add_variable(self.idx, "Hot end fan ON", ua.Variant(False, ua.VariantType.Boolean))
        await printerHotendObj.add_variable(self.idx, "Piece cooling fan speed", 0.0)

        #      frame
        printerFrameObj = await printerSystemObj.add_object(self.idx, "Frame")
        await printerFrameObj.add_variable(self.idx, "Filament present", ua.Variant(False, ua.VariantType.Boolean))
        await printerFrameObj.add_variable(self.idx, "Chamber temperature", 0.0)
        await printerFrameObj.add_variable(self.idx, 'Controller fan ON', ua.Variant(False, ua.VariantType.Boolean))

        #      spool
        printerSpoolObj = await printerSystemObj.add_object(self.idx, "Spool") # Structure from OpenTag spec. https://github.com/Bambu-Research-Group/RFID-Tag-Guide/blob/main/OpenTag.md
        await printerSpoolObj.add_property(self.idx, "Tag version", 0)
        await printerSpoolObj.add_property(self.idx, "Filament Manufacturer", ua.Variant('', ua.VariantType.String))
        await printerSpoolObj.add_property(self.idx, "Material name", ua.Variant('', ua.VariantType.String))
        await printerSpoolObj.add_property(self.idx, "Color Name", ua.Variant('', ua.VariantType.String))
        await printerSpoolObj.add_property(self.idx, "Diameter", 0)
        await printerSpoolObj.add_property(self.idx, "Weight (nominal)", 0)
        await printerSpoolObj.add_property(self.idx, "Print Temp (C)", 0)
        await printerSpoolObj.add_property(self.idx, "Bed Temp (C)", 0)
        await printerSpoolObj.add_property(self.idx, "Density", 0)
        await printerSpoolObj.add_property(self.idx, "Color Hex", 0x000000)
        await printerSpoolObj.add_variable(self.idx, "Filament weight (measured)", 0)
        await printerSpoolObj.add_variable(self.idx, "Filament length (measured)", 0)
        
        #   job object
        printerJobObj = await self.printerObj.add_object(self.idx, "Job")
        await printerJobObj.add_variable(self.idx, "State", ua.Variant('', ua.VariantType.String))
        await printerJobObj.add_variable(self.idx, "Filename", ua.Variant('', ua.VariantType.String))
        await printerJobObj.add_variable(self.idx, "Total job duration [s]", 0.0)
        await printerJobObj.add_variable(self.idx, "Job print time spent [s]", 0.0)

        #   actions
        printerActionObj = await self.printerObj.add_object(self.idx, "Actions")
        await printerActionObj.add_method(
            ua.NodeId("Querry enstops", self.idx),
            ua.QualifiedName("Querry enstops", self.idx),
            self.query_endstops,
            [],
            [ua.VariantType.Boolean, ua.VariantType.Boolean, ua.VariantType.Boolean]
        )

        await printerActionObj.add_method(
            ua.NodeId("Set extruder tempertature", self.idx),
            ua.QualifiedName("Set extruder tempertature", self.idx),
            self.set_extruder_temperature,
            [ua.VariantType.Double],
            [ua.VariantType.String]
        )

        await printerActionObj.add_method(
            ua.NodeId("Set bed tempertature", self.idx),
            ua.QualifiedName("Set bed tempertature", self.idx),
            self.set_bed_temperature,
            [ua.VariantType.Double],
            [ua.VariantType.String]
        )

        await printerActionObj.add_method(
            ua.NodeId("Start job", self.idx),
            ua.QualifiedName("Start job", self.idx),
            self.start_printing,
            [ua.VariantType.String],
            [ua.VariantType.String]
        )

        await printerActionObj.add_method(
            ua.NodeId("Home all axis", self.idx),
            ua.QualifiedName("Home all axis", self.idx),
            self.home_all_axes,
            [],
            [ua.VariantType.String]
        )

        # Finally try to get the printer info
        future = self.get_printer_info_client_.call_async(GetPrinterInfo.Request())
        future.add_done_callback(self.process_printer_info_msg)





async def run(args=None):
    rclpy.init(args=args)
    bridge = OpcuaBridge()
    await bridge.setup_address_space()
    async with bridge.server:
        while rclpy.ok():
            rclpy.spin_once(bridge, timeout_sec=0)
            await asyncio.sleep(1e-4)
        


def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        asyncio.ensure_future(run(), loop=loop)
        loop.run_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
    
