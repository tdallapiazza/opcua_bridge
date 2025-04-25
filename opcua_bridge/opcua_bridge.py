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

from printer_interfaces.msg import PrinterState, HeaterBed, Extruder
from printer_interfaces.srv import GetPrinterInfo, QueryEndStops

class OpcuaBridge(Node):

    def __init__(self):
        super().__init__('opcua_bridge')

        # setup our opc server
        self.server = Server()
        self.endpoint='opc.tcp://0.0.0.0:4840/freeopcua/server/'
        self.uri='http://automation.ceff.ch'

        self.printerObj = None

        self.printer_state_sub_ = self.create_subscription(
            PrinterState,
            'moonraker_bridge/status/state',
            self.update_printer_state,
            10)
        self.printer_state_sub_  # prevent unused variable warning
        self.heater_bed_sub_ = self.create_subscription(
            HeaterBed,
            'moonraker_bridge/status/heater_bed',
            self.update_heater_bed,
            10)
        self.heater_bed_sub_  # prevent unused variable warning
        self.extruder_sub_ = self.create_subscription(
            Extruder,
            'moonraker_bridge/status/extruder',
            self.update_extruder,
            10)
        self.extruder_sub_  # prevent unused variable warning

        # wait for service to be available
        self.get_printer_info_client_ = self.create_client(GetPrinterInfo, 'moonraker_bridge/commands/get_printer_info')
        self.query_end_stops_client_ = self.create_client(QueryEndStops, 'moonraker_bridge/commands/query_endstops')
        while not self.get_printer_info_client_.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('service not available, waiting again...')
        while not self.query_end_stops_client_.wait_for_service(timeout_sec=1.0):
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

    async def process_query_endstops_msg(self, future: Future):
        self.get_logger().info('Query endstops future done.')
        response=future.result()
        if response is not None:
            res= f"x:{response.x}, y:{response.y}, z:{response.z}"
            self.get_logger().info('Query endstops response is: %s' % (res))

            my_node = await self.printerObj.get_child([f'{self.idx}:Systems', f'{self.idx}:Frame', f'{self.idx}:X endstop triggered'])
            if response.x == 'TRIGGERED':
                await my_node.set_value(True)
            else:
                await my_node.set_value(False)
            
            my_node = await self.printerObj.get_child([f'{self.idx}:Systems', f'{self.idx}:Frame', f'{self.idx}:Y endstop triggered'])
            if response.y == 'TRIGGERED':
                await my_node.set_value(True)
            else:
                await my_node.set_value(False)

            my_node = await self.printerObj.get_child([f'{self.idx}:Systems', f'{self.idx}:Frame', f'{self.idx}:Z endstop triggered'])
            if response.z == 'TRIGGERED':
                await my_node.set_value(True)
            else:
                await my_node.set_value(False)
        else:
            self.get_logger().warning('The query_endstops response is empty...')
    
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

    @uamethod
    async def query_endstops(self, parent):
        self.get_logger().info('Querying endstops status')
        future = self.query_end_stops_client_.call_async(QueryEndStops.Request())
        future.add_done_callback(self.process_query_endstops_msg)
        return 'Query sent and executed asyncronously. Result might take time to return.'
    
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
        await printerFrameObj.add_variable(self.idx, "X endstop triggered", ua.Variant(False, ua.VariantType.Boolean))
        await printerFrameObj.add_variable(self.idx, "Y endstop triggered", ua.Variant(False, ua.VariantType.Boolean))
        await printerFrameObj.add_variable(self.idx, "Z endstop triggered", ua.Variant(False, ua.VariantType.Boolean))
        await printerFrameObj.add_variable(self.idx, "Chamber temperature", 0.0)

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
        await printerJobObj.add_variable(self.idx, "State message", ua.Variant('', ua.VariantType.String))
        await printerJobObj.add_variable(self.idx, "Total job duration [s]", 0.0)
        await printerJobObj.add_variable(self.idx, "Job print time spent [s]", 0.0)

        #   actions
        printerActionObj = await self.printerObj.add_object(self.idx, "Actions")
        await printerActionObj.add_method(
            ua.NodeId("Querry enstops", self.idx),
            ua.QualifiedName("Querry enstops", self.idx),
            self.query_endstops,
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
    
