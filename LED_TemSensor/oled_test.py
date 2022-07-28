# oled2.py
from luma.core.interface.serial import i2c, spi
from luma.core.render import canvas
from luma.oled.device import ssd1306, ssd1325, ssd1331, sh1106
import time
import socket
import fcntl
import struct

serial = i2c(port=1, address=0x3C)
oled = sh1106(serial)


def getIP(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15].encode('utf-8'))
    )[20:24])

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


def oledIP():
    with canvas(oled) as draw:
        draw.text((2, 5), "IP: " +  get_host_ip() + '\n' + "I'm working\nbut no people", fill=255)


def oledinit():
    serial = i2c(port=1, address=0x3C)
    oled = sh1106(serial)


def oleddisplay(In, x, y):
    with canvas(oled) as draw:
        # draw.rectangle(device.bounding_box, outline="white", fill="black")
        draw.text((x, y), In, fill="white")

'''
if __name__ == "__main__":
    oledinit()
    # oledIP()
    In = "hello "
    oleddisplay(In, 15, 20)
    '''
if __name__ == "__main__":
    oledinit()
    i=10
    while (i>0):
        i-=1
        oledIP()
        time.sleep(1.0)
        localtime = time.asctime(time.localtime(time.time()))
        In = "hello limin " + "\n" + localtime
        oleddisplay(In, 15, 20)
        time.sleep(3.0)




