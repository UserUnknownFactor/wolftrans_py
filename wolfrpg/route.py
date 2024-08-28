# -*- coding: utf-8 -*-
from .filecoder import FileCoder

class RouteCommand():
    TERMINATOR = bytes([0x01, 0x00])

    def __init__(self, _id, args):
        self._id = _id
        self.args = args

    @staticmethod
    def create(coder):
        # Read all data for this movement command from file
        _id = coder.read_u1()
        args_len = coder.read_u1()
        _args = [coder.read_u4() for _ in range(args_len)]
        coder.verify(RouteCommand.TERMINATOR)

        #TODO Create proper route command
        return RouteCommand(_id, _args)

    def write(self, coder):
        coder.write_u1(self._id)
        coder.write_u1(len(self.args))
        for arg in self.args:
            coder.write_u4(arg)
        coder.write(RouteCommand.TERMINATOR)

