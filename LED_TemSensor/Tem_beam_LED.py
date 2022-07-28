# -*- coding: utf-8 -*-
import time, os, sys,datetime
# beam status and temperature on OLED
from luma.core.interface.serial import i2c, spi
from luma.core.render import canvas
from luma.oled.device import ssd1306, ssd1325, ssd1331, sh1106
import socket, requests
import fcntl
import struct
from bs4 import BeautifulSoup
from smbus2 import SMBus

# BME280 iic address.
BME280_I2C_ADDRESS = 0x76  # SDO = 0

# Registers value                # BME280 ID
BME280_ID_Value = 0x60  # BME280 ID
BME280_RESET_VALUE = 0xB6

# BME280 Registers definition
BME280_HUM_LSB_REG = 0xFE  # Humidity LSB Register
BME280_HUM_MSB_REG = 0xFD  # Humidity MSB Register
BME280_TEMP_XLSB_REG = 0xFC  # Temperature XLSB Register
BME280_TEMP_LSB_REG = 0xFB  # Temperature LSB Register
BME280_TEMP_MSB_REG = 0xFA  # Temperature LSB Register
BME280_PRESS_XLSB_REG = 0xF9  # Pressure XLSB  Register
BME280_PRESS_LSB_REG = 0xF8  # Pressure LSB Register
BME280_PRESS_MSB_REG = 0xF7  # Pressure MSB Register
BME280_CONFIG_REG = 0xF5  # Configuration Register
BME280_CTRL_MEAS_REG = 0xF4  # Ctrl Measure Register
BME280_CTRL_HUM_REG = 0xF2  # Ctrl humidity Measure Register
BME280_STATUS_REG = 0xF3  # Status Register
BME280_RESET_REG = 0xE0  # Soft reset Register
BME280_ID_REG = 0xD0  # Chip ID Register

# calibration parameters
BME280_DIG_T1_LSB_REG = 0x88
BME280_DIG_T1_MSB_REG = 0x89
BME280_DIG_T2_LSB_REG = 0x8A
BME280_DIG_T2_MSB_REG = 0x8B
BME280_DIG_T3_LSB_REG = 0x8C
BME280_DIG_T3_MSB_REG = 0x8D
BME280_DIG_P1_LSB_REG = 0x8E
BME280_DIG_P1_MSB_REG = 0x8F
BME280_DIG_P2_LSB_REG = 0x90
BME280_DIG_P2_MSB_REG = 0x91
BME280_DIG_P3_LSB_REG = 0x92
BME280_DIG_P3_MSB_REG = 0x93
BME280_DIG_P4_LSB_REG = 0x94
BME280_DIG_P4_MSB_REG = 0x95
BME280_DIG_P5_LSB_REG = 0x96
BME280_DIG_P5_MSB_REG = 0x97
BME280_DIG_P6_LSB_REG = 0x98
BME280_DIG_P6_MSB_REG = 0x99
BME280_DIG_P7_LSB_REG = 0x9A
BME280_DIG_P7_MSB_REG = 0x9B
BME280_DIG_P8_LSB_REG = 0x9C
BME280_DIG_P8_MSB_REG = 0x9D
BME280_DIG_P9_LSB_REG = 0x9E
BME280_DIG_P9_MSB_REG = 0x9F
BME280_DIG_H1_REG = 0xA1
BME280_DIG_H2_LSB_REG = 0xE1
BME280_DIG_H2_MSB_REG = 0xE2
BME280_DIG_H3_REG = 0xE3
BME280_DIG_H4_H8_REG = 0xE4  # DIG_H4[11:4]/[3:0]=0xE4/0xE5[3:0]
BME280_DIG_H4_L4_REG = 0xE5  # 0xE5[3:0]
BME280_DIG_H5_H4_REG = 0xE5  # 0xE5[7:4]
BME280_DIG_H5_L8_REG = 0xE6  # DIG_H5[11:4]/[3:0]=0xE5[7:4]/0xE6
BME280_DIG_H6_REG = 0xE7


class BME180(object):
    def __init__(self, address=BME280_I2C_ADDRESS):
        self._address = address
        self._bus = SMBus(1)  # 1: iic编号为1（根据自己的硬件接口选择对应的编号）
        # Load calibration values.
        print('read byte:\n')
        print(self._read_byte(BME280_ID_REG))
        if self._read_byte(BME280_ID_REG) == BME280_ID_Value:  # read BME280 id
            self._load_calibration()  # load calibration data
            # BME280_T_MODE_1 << 5 | BME280_P_MODE_1 << 2 | BME280_SLEEP_MODE;
            ctrlmeas = 0xFF
            # BME280_T_SB1 << 5 | BME280_FILTER_MODE_1 << 2;
            config = 0x14
            self._write_byte(BME280_CTRL_MEAS_REG, ctrlmeas)  # write BME280 config
            # sets the data acquisition options
            self._write_byte(BME280_CONFIG_REG, config)
        else:
            print("Read BME280 id error!\r\n")

    def _read_byte(self, cmd):
        return self._bus.read_byte_data(self._address, cmd)

    def _read_u16(self, cmd):
        LSB = self._bus.read_byte_data(self._address, cmd)
        MSB = self._bus.read_byte_data(self._address, cmd + 1)
        return (MSB << 8) + LSB

    def _read_s16(self, cmd):
        result = self._read_u16(cmd)
        if result > 32767:
            result -= 65536
        return result

    def _write_byte(self, cmd, val):
        self._bus.write_byte_data(self._address, cmd, val)

    def _load_calibration(self):  # load calibration data
        "load calibration"

        """ read the temperature calibration parameters """
        self.dig_T1 = self._read_u16(BME280_DIG_T1_LSB_REG)
        self.dig_T2 = self._read_s16(BME280_DIG_T2_LSB_REG)
        self.dig_T3 = self._read_s16(BME280_DIG_T3_LSB_REG)
        """ read the pressure calibration parameters """
        self.dig_P1 = self._read_u16(BME280_DIG_P1_LSB_REG)
        self.dig_P2 = self._read_s16(BME280_DIG_P2_LSB_REG)
        self.dig_P3 = self._read_s16(BME280_DIG_P3_LSB_REG)
        self.dig_P4 = self._read_s16(BME280_DIG_P4_LSB_REG)
        self.dig_P5 = self._read_s16(BME280_DIG_P5_LSB_REG)
        self.dig_P6 = self._read_s16(BME280_DIG_P6_LSB_REG)
        self.dig_P7 = self._read_s16(BME280_DIG_P7_LSB_REG)
        self.dig_P8 = self._read_s16(BME280_DIG_P8_LSB_REG)
        self.dig_P9 = self._read_s16(BME280_DIG_P9_LSB_REG)
        """ read the humidity calibration parameters """
        self.dig_H1 = self._read_byte(BME280_DIG_H1_REG)
        self.dig_H2 = self._read_s16(BME280_DIG_H2_LSB_REG)
        self.dig_H3 = self._read_byte(BME280_DIG_H3_REG)
        self.dig_H4 = (self._read_byte(BME280_DIG_H4_H8_REG) << 4) + (self._read_byte(BME280_DIG_H4_L4_REG) & 0xf)
        self.dig_H5 = (self._read_byte(BME280_DIG_H5_H4_REG) >> 4) + (self._read_byte(BME280_DIG_H5_L8_REG) << 4)
        self.dig_H6 = self._read_byte(BME280_DIG_H6_REG)
        print(f'H1={self.dig_H1}\n,H2={self.dig_H2}\n,H3={self.dig_H3}\n,H4={self.dig_H4}\n,'
              f'H5={self.dig_H5}\n,H6={self.dig_H6}\n')

    def compensate_temperature(self, adc_T):
        """Returns temperature in DegC, double precision. Output value of "1.23"equals 51.23 DegC."""
        var1 = ((adc_T) / 16384.0 - (self.dig_T1) / 1024.0) * (self.dig_T2)
        var2 = (((adc_T) / 131072.0 - (self.dig_T1) / 8192.0) *
                ((adc_T) / 131072.0 - (self.dig_T1) / 8192.0)) * (self.dig_T3)
        self.t_fine = var1 + var2
        temperature = (var1 + var2) / 5120.0
        return temperature

    def compensate_pressure(self, adc_P):
        """Returns pressure in Pa as double. Output value of "6386.2"equals 96386.2 Pa = 963.862 hPa."""
        var1 = (self.t_fine / 2.0) - 64000.0
        var2 = var1 * var1 * (self.dig_P6) / 32768.0
        var2 = var2 + var1 * (self.dig_P5) * 2.0
        var2 = (var2 / 4.0) + ((self.dig_P4) * 65536.0)
        var1 = ((self.dig_P3) * var1 * var1 / 524288.0 +
                (self.dig_P2) * var1) / 524288.0
        var1 = (1.0 + var1 / 32768.0) * (self.dig_P1)

        if var1 == 0.0:
            return 0  # avoid exception caused by division by zero

        pressure = 1048576.0 - adc_P
        pressure = (pressure - (var2 / 4096.0)) * 6250.0 / var1
        var1 = (self.dig_P9) * pressure * pressure / 2147483648.0
        var2 = pressure * (self.dig_P8) / 32768.0
        pressure = pressure + (var1 + var2 + (self.dig_P7)) / 16.0

        return pressure

    def compensate_humidity(self, adc_H):
        """
        compensate the readout value,return humidity
        Returns humidity in %RH as unsigned 32 bit integer in Q22.10 format (22 integer and 10
        fractional bits).
        Output value of “47445” represents 47445/1024 = 46.333 %RH
        :param adc_H:
        :return:
        """
        v_x1_u32r = (self.t_fine - 76800)
        v_x1_u32r = (((((adc_H * 2 ** 14) - (self.dig_H4 * 2 ** 20) - (self.dig_H5 * v_x1_u32r)) + 16384) / 2 ** 15) * (
                ((((((
                             v_x1_u32r * self.dig_H6) / 2 ** 10) * (
                            ((v_x1_u32r * self.dig_H3) / 2 ** 11) + 32786)) / 2 ** 10) + 2097152)
                 * self.dig_H2 + 8192) / 2 ** 14))
        v_x1_u32r = (v_x1_u32r - (((((v_x1_u32r / 2 ** 15) * (v_x1_u32r / 2 ** 15)) / 2 ** 17) * self.dig_H1) / 2 ** 4))
        v_x1_u32r = 0 if v_x1_u32r < 0 else v_x1_u32r
        v_x1_u32r = 419430400 if v_x1_u32r > 419430400 else v_x1_u32r
        return v_x1_u32r / 4096

    def get_temperature_and_pressure_humidity(self):
        """Returns pressure in Pa as double. Output value of "6386.2"equals 96386.2 Pa = 963.862 hPa."""
        xlsb = self._read_byte(BME280_TEMP_XLSB_REG)
        lsb = self._read_byte(BME280_TEMP_LSB_REG)
        msb = self._read_byte(BME280_TEMP_MSB_REG)

        adc_T = (msb << 12) | (lsb << 4) | (
                xlsb >> 4)  # temperature registers data
        temperature = self.compensate_temperature(
            adc_T)  # temperature compensate

        xlsb = self._read_byte(BME280_PRESS_XLSB_REG)
        lsb = self._read_byte(BME280_PRESS_LSB_REG)
        msb = self._read_byte(BME280_PRESS_MSB_REG)

        adc_P = (msb << 12) | (lsb << 4) | (
                xlsb >> 4)  # pressure registers data
        pressure = self.compensate_pressure(
            adc_P)  # pressure compensate

        lsb = self._read_byte(BME280_HUM_LSB_REG)
        msb = self._read_byte(BME280_HUM_MSB_REG)

        adc_H = (msb << 8) | lsb  # raw humidity registers data
        print(f'raw adc_H={adc_H}')
        humidity = self.compensate_humidity(
            adc_H)  # pressure compensate
        return temperature, pressure / 1000, humidity / 1024


# OLED sh1106 by I2c protocol
serial = i2c(port=1, address=0x3C)
oled = sh1106(serial)


def getIP(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    IP = socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15].encode('utf-8'))
    )[20:24])
    s.close()
    return IP

def get_host_ip():
    """
    查询本机ip地址
    :return:
    """
    try:
        s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        s.connect(('8.8.8.8',80))
        ip=s.getsockname()[0]
    finally:
        s.close()
 
    return ip


def oledIP_beam(IP, info):
    with canvas(oled) as draw:
        draw.text((0, 5), "IP: " + str(IP) + '\n' + info, fill=255)


def oledinit():
    serial = i2c(port=1, address=0x3C)
    oled = sh1106(serial)


def oleddisplay(In, x, y):
    with canvas(oled) as draw:
        # draw.rectangle(device.bounding_box, outline="white", fill="black")
        draw.text((x, y), In, fill="white")


def download_url(url, num_retries=5):
    """
    download url
    :param url:
    :param num_retries:
    :return: html in text
    """
    headers = {'User-Agent': 'SSRF_test', 'Connection': 'close'}
    try:
        with requests.Session() as s:
            resp = s.get(url, headers=headers, proxies=None, timeout=10)
            html = resp.text
            s.close()
        if resp.status_code >= 400:
            print('Download error:', resp.text)
            html = None
            if num_retries and 500 <= resp.status_code < 600:
                # recursively retry 5xx HTTP errors
                return download_url(url, num_retries - 1)
    except requests.exceptions.RequestException as e:
        print('Download error:', e)
        html = None
    return html

def get_datetime():
    """ get current date time, as accurate as milliseconds

        Args: None

        Returns:
            str type '%Y-%m-%d %H:%M:%S.%f'
            eg: "2018-10-01 00:32:39.993176"

    """
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    print(timestamp)
    return str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

def get_beamcurrent(html):
    soup = BeautifulSoup(html, 'html.parser')
    # title = soup.title.text

    text_info = soup.text.split('\n')
    text_info = [t for t in text_info if t != '']
    # find the current and other information
    Current = text_info[text_info.index('Current:') + 1]
    print('Current:' + Current)
    Operation_info = text_info[text_info.index('Orbit(rms)x/y:') + 2]
    print(Operation_info)
    [plan, light] = [Operation_info.split('light:')[0].split(':')[-1], Operation_info.split('light:')[-1]]
    print([plan, light])
    return Current, plan, light


# check file in filepath or not
def creatPath(file_path):
    """
    create a given path if not exist and return it
    :param file_path:
    :return: file_path
    """
    if os.path.exists(file_path) is False:
        os.makedirs(file_path)
    return file_path


def to_log(text, filename, path):
    """
    save  data to log file
    :param text:str text to write
    :param filename: filename end with .text .dat .log
    :param path: path to file
    :return: None
    """
    filepath = os.path.join(path, filename)
    with open(filepath, 'a+') as f:
        f.write(text + '\n')
        # f.close()


if __name__ == "__main__":
    # BME280 initialize
    ATM_P = 101.33
    print("BME280 Test Program ...\n")
    BME280 = BME180()
    t0 = time.time()
    # data save folder
    save_path = os.path.join(os.getcwd(), 'SavedData')
    creatPath(save_path)
    startTime = time.time()
    Note = 'Temperature data by degree' + '\n' + 'StartTime: ' + time.asctime() + '\n'
    Tem_header = 'Time'+'\t\t'+ 'Elapsed Time/s' + '\t' + 'T_ambient(C)' + '\t' + 'Pressure(kPa)' + '\t' + 'humidity%'+'\t\t'+'Height(m)'
    print(Tem_header)
    to_log(Note + Tem_header, 'Tem_data_Led.dat', save_path)
    # save beam info
    beam_http = 'http://159.226.222.249/ssrf/beam/'
    beam_head = 'StartTime:' + time.asctime() + '\n' 'Time'+'\t\t'+ 'Elapsed Time/s' + '\t' + 'BeamCurrent' + '\t' + 'shift plan' + '\t' + 'light'
    to_log(beam_head, 'beam_status_Led.dat', save_path)
    i = 0
    #IP = getIP("wlan0")
    IP=get_host_ip()
    beam_html = download_url(beam_http, num_retries=5)
    while time.time() - t0 < 100000:
        time.sleep(1)
        T, P, H = BME280.get_temperature_and_pressure_humidity()
        print(f'Temperature = {T:.2f} C Pressure = {P:.4f}kPa humidity={H:.3f}%')
        print(f'Height={(ATM_P - P) * 1000 / 133 * 12:.2f}m')
        height=(ATM_P - P) * 1000 / 133 * 12
        beam_html = download_url(beam_http, num_retries=5)
        if beam_html:
            beam_info = get_beamcurrent(beam_html)
        else:
            beam_info = ('error', 'error', 'error')
        # show time
        cur_time = get_datetime()
        my_note='RaspberryPi 4B\n&Limin@Cynthnia&\nHave a Good Day'
        my_info = my_note+'\n'+cur_time
        oleddisplay(my_info, 0, 2)
        time.sleep(3.0)
        # show beam info
        beam_note = 'BeamCurrent:' + beam_info[0] + '\n' + beam_info[1] + '\n' + beam_info[2]
        oledIP_beam(IP, beam_note)
        time.sleep(2.5)
        # show Tem info
        Tem=f'T= {T:.2f} C\nP = {P:.2f} kPa\nhumidity={H:.2f} %\nheight={height:.2f} m'
        oleddisplay(Tem, 0, 2)
        time.sleep(2.5)
        # save to log file
        elapsedTime = '%.2f' % (time.time() - startTime)
        Tem_info = '%s\t%s\t \t %.2f\t \t%.3f\t \t%.2f\t \t%.2f\t' %(cur_time,elapsedTime,T,P,H,height)
        to_log(Tem_info,'Tem_data_Led.dat', save_path)
        beam_parameter = '%s\t%s\t \t %s\t  \t%s\t%s' % (cur_time,elapsedTime, beam_info[0], beam_info[1], beam_info[2])
        to_log(beam_parameter, 'beam_status_Led.dat', save_path)
