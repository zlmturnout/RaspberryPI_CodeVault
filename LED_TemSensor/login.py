import os,requests,time,socket
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
    
def login():
    headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36'}
    se=requests.Session()
    url='http://192.168.195.6/drcom/login?callback=dr1663836985777&DDDDD=zhoulimin&upass=Vertical@153&0MKKey=123456&R1=0&R3=0&R6=0&para=00&v6ip=&_=1663836943100'
    r=requests.get(url,headers=headers)
    Host_IP=get_host_ip()   
    print(f'get current host ip={Host_IP}')