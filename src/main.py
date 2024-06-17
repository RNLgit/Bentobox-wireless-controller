import time
import network
import socket
from machine import ADC, Pin
from web import html

f_cfg = open("config.cfg", "r")
ssid = f_cfg.readline().strip().split("=")[1]
password = f_cfg.readline().strip().split("=")[1]
f_cfg.close()

fan_ctrl = Pin(17, Pin.OUT)
fan_button = Pin(15, Pin.IN, Pin.PULL_UP)
fan_adc = ADC(Pin(26))


def wifi_setup(ssid: str, password: str) -> network.WLAN:
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    time.sleep(3)  # wait for wlan chip to power up
    ts = time.time()
    while time.time() - ts < 60:
        try:
            next(i for i, *_ in wlan.scan() if i.decode() == ssid)
            print(f"found ssid: {ssid}")
            break
        except StopIteration:
            print(f"ssid: {ssid} (type:{type(ssid)}) not found, retrying...")
            time.sleep(1)
    wlan.connect(ssid, password)

    max_wait = 60  # Wait for connect or fail
    while max_wait > 0:
        # if wlan.status() < 0 or wlan.status() >= 3:
        if wlan.isconnected():
            break
        max_wait -= 1
        print(f"waiting for connection... retry countdown: {max_wait}")
        time.sleep(1)

    if wlan.status() != 3:  # Handle connection error
        raise RuntimeError(f"network connection failed, err: {wlan.status()}")
    else:
        wlan_ip, wlan_subnet_mask, wlan_gateway, wlan_dns_server = wlan.ifconfig()
        print(f"Connected, ip: {wlan_ip}")
        return wlan


def fan_on_off(req: str) -> None:
    fan_on = req.find("fan=turn_on")
    fan_off = req.find("fan=turn_off")

    if not fan_on == -1 and not fan_off == -1:
        print(f"Error, both buttons detected, REST request: fan=turn_on: {fan_on}, fan=turn_off: {fan_off}")
    elif not fan_off == -1:
        print("Turning off Bentobox Fan.")
        fan_ctrl.value(0)
    elif not fan_on == -1:
        print("Turning on Bentobox Fan.")
        fan_ctrl.value(1)
    else:
        print(f"Incorrect REST request detected. REST request: fan=turn_on: {fan_on}, fan=turn_off: {fan_off}")


def read_adc() -> float:
    analog_value = fan_adc.read_u16()
    voltage = analog_value * (3.3 / 65535)
    return (4.75 + 10 + 10) / 4.75 * voltage


wlan = wifi_setup(ssid, password)


# Open socket
addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
s = socket.socket()
s.bind(addr)
s.listen(1)
print("listening on", addr)

# Listen for connections, serve client
while True:
    try:
        cl, addr = s.accept()
        print("client connected from", addr)
        request = cl.recv(1024)
        request = request.decode()
        print(f"request: {request}")
        req, *_ = request.split("\n")  # request REST

        fan_on_off(req)

        fan_state = "FAN is OFF" if fan_ctrl.value() == 0 else "FAN is ON"

        # Create and send response
        stat_string = f"{fan_state}<br>ADC reading: {round(read_adc(), 3)}V"
        response = html % stat_string
        cl.send("HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n")
        cl.send(response)
        cl.close()

    except OSError as e:
        cl.close()
        print("connection closed")
