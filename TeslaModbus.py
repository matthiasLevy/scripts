# Some references here
# http://riptideio.github.io/pymodbus/

# from pymodbus.client.sync import ModbusTcpClient
from pymodbus.client.tcp import ModbusTcpClient
from pymodbus.payload import BinaryPayloadDecoder, BinaryPayloadBuilder
from pymodbus.client.base import ConnectionException
from pymodbus.constants import Endian

# client = ModbusTcpClient('127.0.0.1', port=11502, timeout=5)
# client.connect()

class TSC_connector:
    """Simple interface to TSC in Modbus TCP"""

    ADDRESS = dict(
        P_up=dict(address=1024, type='int32'),
        P_down=dict(address=1026, type='int32'),
        Q_up=dict(address=1224, type='int32'),
        Q_down=dict(address=1226, type='int32'),
        real_power_mode=dict(address=1000, type='uint16'),
        always_active=dict(address=1001, type='bool'),
        peak_power_mode=dict(address=1002, type='uint16'),
        P_setpoint=dict(address=1020, type='int32'),
        reactive_active_priority=dict(address=1201, type='uint16'),
        reactive_power_mode=dict(address=1200, type='uint16'),
        Q_setpoint=dict(address=1220, type='int32'),
        full_pack_energy=dict(address=205, type='int32'),
        energy_remaining=dict(address=207, type='int32'),
        energy_remaining_nominal=dict(address=207, type='int32'),
        Number_Available_Megapacks=dict(address=218, type='int16'),
    )
    ramps_names = ['P_up', 'P_down', 'Q_up', 'Q_down']

    INT_TYPES = dict(
        int32=dict(number=32, signed=True),
        int16=dict(number=16, signed=True),
        uint32=dict(number=32, signed=False),
        uint16=dict(number=16, signed=False),
    )

    def __init__(self, ip='127.0.0.1', port=11502, timeout=5):
        """default is 502, but using ssh port forwarding"""
        self.client = ModbusTcpClient(ip, port=port, timeout=timeout)

    def connect(self):
        if not self.client.connected:
            self.client.connect()

    def close(self):
        if self.client.connected:
            self.client.close()

    def _base_reader(self, address, number):
        """base Modbus reader and decoder"""
        self.connect()

        result = self.client.read_input_registers(address, int(number / 2))
        if not result.isError():
            return BinaryPayloadDecoder.fromRegisters(
                result.registers,
                byteorder=Endian.Big,
                wordorder=Endian.Big
                #### for int only ?
            )
        else:
            raise ConnectionException

    def _base_writer(self, address, value, type):
        """base Modbus encoder and writer"""

        builder = BinaryPayloadBuilder(byteorder=Endian.Big, wordorder=Endian.Big)
        if 'str' in type:
            builder.add_string(value)
        elif type == 'int16':
            builder.add_16bit_int(value)
        elif type == 'uint16':
            builder.add_16bit_uint(value)
        elif type == 'int32':
            builder.add_32bit_int(value)
        elif type == 'uint32':
            builder.add_32bit_uint(value)
        payload = builder.build()

        if not self.client.connected:
            self.client.connect()

        self.connect()
        result = self.client.write_registers(
            address, payload, count=len(payload), skip_encode=True
        )
        if not result.isError():
            return True
        else:
            return False

    def read_string_raw(self, address, type):
        # number is 16 or 32
        if '16' in type:
            number = 16
        elif '32' in type:
            number = 32
        else:
            raise TypeError("Wrong type for string reading")
        return (
            self._base_reader(address, number).decode_string(32).decode().rstrip('x\00')
        )

    def read_type(self, address, type):
        if type == 'bool':
            type = 'uint16'
        if 'int' in type:
            return self.read_int(address, type)
        elif 'str' in type:
            return self.read_string_raw(address, type)

    def read_int(self, address, type: str):
        return self.read_int_raw(address, **self.INT_TYPES[type])

    def read_val(self, val: str):
        if val in self.ADDRESS:
            address, type = self.ADDRESS[val].values()
            return self.read_type(address, type)
        else:
            print(
                f"Wrong value asked for reading: {val}, expected {self.ADDRESS.keys()}"
            )
        return None

    def read_int_raw(self, address, number, signed=False):
        # number is 16 or 32
        decoder = self._base_reader(address, number)
        if signed:
            if number == 16:
                return decoder.decode_16bit_int()
            else:
                return decoder.decode_32bit_int()
        else:
            if number == 16:
                return decoder.decode_16bit_uint()
            else:
                return decoder.decode_32bit_uint()

    def read_bool(self, address):
        return self.read_int_raw(address, 16, False)

    def read_energy(self):
        return self.read_int_raw(207, 32, True)

    def read_ramps(self):
        return dict(
            [
                (k, self.read_int(self.ADDRESS[k]['address'], self.ADDRESS[k]['type']))
                for k in self.ramps_names
            ]
        )

    def read_ramps_MW_minute(self):
        ramps = self.read_ramps()
        for k, v in ramps.items():
            ramps[k] = v * 60 / 1e6
        return ramps

    def write_registers(self, address, value, type):
        return self._base_writer(address, value, type)

    def change_ramps(self, ramps: dict):
        for k, v in ramps.items():
            if k in self.ramps_names:
                address = self.ADDRESS[k]['address']
                type = self.ADDRESS[k]['type']

                ret = self.write_registers(address, v, type)
                if not ret:
                    print(f"Error writing {k}: {v}")
            else:
                print(f"Wrong key for ramp update: {k}, expected {self.ramps_names}")


if __name__ == '__main__':
    tsc_connector = TSC_connector()

    # Number of Megapacks
    client.read_holding_registers(101, 1).getRegister(0)

    # Tesla Site Controller Firmware Version
    tsc_connector.read_string(102, 16)

    # Energy remaining
    result = client.read_input_registers(207, 2)

    # Always active
    tsc_connector.read_bool(1001)

    print(result.bits[0])
    client.close()
