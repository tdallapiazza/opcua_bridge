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

from printer_interfaces.msg import PrinterState

class OpcuaBridge(Node):

    def __init__(self):
        super().__init__('opcua_bridge')

        # setup our opc server
        self.server = Server()
        self.endpoint='opc.tcp://0.0.0.0:4840/freeopcua/server/'
        self.uri='http://automation.ceff.ch'

        self.printer_state_sub_ = self.create_subscription(
            PrinterState,
            'moonraker_bridge/status/state',
            self.update_printer_state,
            10)
        self.printer_state_sub_  # prevent unused variable warning

    async def update_printer_state(self, msg):
        a_node = await self.printerObj.get_child([f"{self.idx}:Info", f"{self.idx}:State"])
        await a_node.set_value(msg.current_state)
        self.get_logger().info('Setting state value to: "%s"' % msg.current_state)
    
    async def setup_address_space(self):
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
        await printerInfoObj.add_property(self.idx, "Name", ua.Variant("", ua.VariantType.String))
        await printerInfoObj.add_property(self.idx, "Manufacturer", ua.Variant('', ua.VariantType.String))
        await printerInfoObj.add_property(self.idx, "Model", ua.Variant('', ua.VariantType.String))
        await printerInfoObj.add_property(self.idx, "Location", ua.Variant('', ua.VariantType.String))
        await printerInfoObj.add_property(self.idx, "CPU info", ua.Variant('', ua.VariantType.String))
        await printerInfoObj.add_variable(self.idx, "State", ua.Variant("", ua.VariantType.String))
        await printerInfoObj.add_variable(self.idx, "State message", ua.Variant("", ua.VariantType.String))





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
    
