from __future__ import print_function
import serial
import time

debug = False

class SyringePump(serial.Serial):
    def __init__(self, port, timeout=0.5, debug=False):
        params = {
                'timeout'  : timeout,
                'baudrate' : 19200,
                'bytesize' : serial.EIGHTBITS,
                'parity'   : serial.PARITY_NONE,
                'stopbits' : serial.STOPBITS_ONE,
                }
        super(SyringePump, self).__init__(port, **params)
        self.debug = debug


    def sendCmd(self, cmd):
        if self.debug:
            print('cmd: {0}'.format(cmd))
        cmd = '{0}\r'.format(cmd)
        self.write(cmd)
        rsp = self.readline()
        self.checkRsp(rsp)
        return rsp


    def checkRsp(self, rsp):
        if self.debug:
            print('rsp: {0}, {1}'.format([x for x in rsp], [ord(x) for x in rsp]))


    def setDiameter(self, val):
        """
        Set the syringe inside diameter in mm. Valid diameters range from
        0.1mm to 50.0mm. If the diameter is set between 0.1 to 14.0 mm then the
        default volume units for the accumulated infusion and withdrawal volumes
        and the "Volume to be dispsensed" will be uL (microlitres). From 14.01
        mm to 50.0 mm the default volume units will be set to mL.
        """
        if val < 0.1 or val > 50.0:
            raise ValueError('syringe diameter out of range')
        valStr = float2PumpFormat(val)
        self.sendCmd('DIA {0}'.format(valStr))


    def setRate(self, val, units='UM'):
        """
        Set the pumping rate.  Value must be bewteen 0 and 1000 and
        units must be 'NS', 'UM', 'MM', 'UH', or 'MH'
        """
        if not units.upper() in ('NS', 'UM', 'MM', 'UH', 'MH'):
            raise ValueError('unknown pumping rate units: {0}'.format(units))
        if units.upper() == 'NS':
            val = 60.0*val/(1.0e3)
            units = 'UM'
        valStr = float2PumpFormat(val)
        self.sendCmd('RAT {0} {1}'.format(valStr,units))


    def setDirection(self, val):
        """
        Set the pump direction - infuse 'INF', or withdraw 'WDR'
        """
        val = val.lower()
        if val in ('infuse', 'inf'):
            valStr = 'INF'
        elif val in ('withdraw', 'wdr'):
            valStr = 'WDR'
        self.sendCmd('DIR {0}'.format(valStr))


    def setAccumUnits(self, units):
        """
        Sets the volume units ML or UL - overides the default value set when the
        syringe diameter is set.
        """
        if not units in ('ML', 'UL'):
            raise ValueError('unknown volume unit: {0}'.format(units))
        self.sendCmd('VOL {0}'.format(units))


    def setVolumeToDispense(self, volume):
        """
        Sets the volume to be dispensed, after which the pump will automatically
        stop. Volume units are dependent on what was set with setAccumUnits, or
        whatever the default is. See setDiameter for default units.
        """
        if isinstance(volume, int) or isinstance(volume, float):
            valStr = float2PumpFormat(volume)
            self.sendCmd('VOL {0}'.format(valStr))


    def clearVolumeAccum(self, accumType='both'):
        """
        Clears the volume accumlator. If accumType == 'INF' then just the
        infused volume accumulator is cleared. If accumType == 'WDR' then just
        the withdrawn volume accumulator is cleared. If accumType='BOTH' then
        both infused and withdrawn volume accumulators are cleared.
        """
        accumType = accumType.lower()
        if accumType in ('inf', 'both'):
            self.sendCmd('CLD INF')
        if accumType in ('wdr', 'both'):
            self.sendCmd('CLD WDR')


    def run(self):
        """
        Start the syringe pump.
        """
        self.sendCmd('RUN')


    def stop(self):
        """
        Stop the syring pump.
        """
        self.sendCmd('STP')


    def getVolumeAccum(self):
        """
        Return the values in the pump volume accumulators. Value is always returned in
        nano liters.
        """
        rsp = self.sendCmd('DIS')
        rsp = [x for x in rsp]
        rsp = rsp[1:-1] # Remove STX and ETX

        # Get volume units
        units = ''.join(rsp[-2:])
        infuse = float(''.join(rsp[4:9]))
        withdraw = float(''.join(rsp[10:15]))

        if units == 'UL':
            scale = 1.0e3
        elif units == 'ML':
            scale = 1.0e6
        else:
            raise IOError('unknown volume unit: {0}'.format(units))
        infuse = scale*infuse
        withdraw = scale*withdraw
        return infuse, withdraw


def float2PumpFormat(val):
    """
    Normalize floating point number into format suitable for sending
    to the syringe pump
    """
    val = float(val)
    if (val < 0) or (val >= 1000):
        raise ValueError('value out of range')
    if val >= 100:
        pumpStr = '{0:3.1f}'.format(val)
    elif val >= 10:
        pumpStr = '{0:2.2f}'.format(val)
    else:
        pumpStr = '{0:1.3f}'.format(val)
    return pumpStr


if __name__ == '__main__':
    print("blah")
