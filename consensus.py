from random import randint
import time
import types.communications as communications
import zmq

class block_proposal:
    def __init__(self) -> None:
        self.data
        self.block_number
        self.already_signed = {}
        self.errors_found = {}
