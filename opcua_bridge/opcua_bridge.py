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

class OpcuaBridge(Node):

    def __init__(self):
        super().__init__('opcua_bridge')

        # setup our opc server
        self.server = Server()
        self.endpoint='opc.tcp://0.0.0.0:4840/freeopcua/server/'
        self.uri='http://automation.ceff.ch'




async def run(args=None):
    rclpy.init(args=args)
    bridge = OpcuaBridge()
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
    
