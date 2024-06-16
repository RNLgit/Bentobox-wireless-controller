import time
import network
import socket
from machine import ADC, Pin
from web import html

ssid = "TP-Link_00EC"
password = "95471624"

fan_ctrl = Pin(17, Pin.OUT)
fan_button = Pin(15, Pin.IN, Pin.PULL_UP)
fan_adc = ADC(Pin(26))


def wifi_setup(ssid: str, password: str) -> network.WLAN:
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    time.sleep(3)  # wait for wlan chip to power up
    ts = time.time()
    while time.time() - ts < 30:
        try:
            next(i for i, *_ in wlan.scan() if i.decode() == ssid)
            print(f"found ssid: {ssid}")
            break
        except StopIteration:
            print(f"ssid: {ssid} not found, retrying...")
            time.sleep(1)
    wlan.connect(ssid, password)

    max_wait = 30  # Wait for connect or fail
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
        print("request:")
        print(request)
        request = str(request)
        # req, *_ = s.split("\n")
        fan_on = request.find("fan=turn_on")
        fan_off = request.find("fan=turn_off")

        print(f"request: fan=turn_on: {fan_on}, fan=turn_off: {fan_off}")

        if not fan_on == -1:
            print("fan on pressed on webpage")
            fan_ctrl.value(1)
        if not fan_off == -1:
            print("fan off pressed on webpage")
            fan_ctrl.value(0)

        fan_state = "FAN is OFF" if fan_ctrl.value() == 0 else "FAN is ON"

        if fan_button.value() == 1:  # button not pressed
            print("button NOT pressed")
            button_state = "Button is NOT pressed"
        else:
            print("button pressed")
            button_state = "Button is pressed"

        # Create and send response
        stat_string = f"{fan_state}\n{button_state}"
        response = html % stat_string
        cl.send("HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n")
        cl.send(response)
        cl.close()

    except OSError as e:
        cl.close()
        print("connection closed")
