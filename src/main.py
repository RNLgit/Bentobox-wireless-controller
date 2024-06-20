import time
import network
import socket
from machine import ADC, Pin, Timer
from web import html

f_cfg = open("config.cfg", "r")
ssid = f_cfg.readline().strip().split("=")[1]
password = f_cfg.readline().strip().split("=")[1]
f_cfg.close()

fan_pin = Pin(17, Pin.OUT)
button_pin = Pin(15, Pin.IN, Pin.PULL_UP)
adc_pin = ADC(Pin(26))
is_fan_on = False
debounce_timer = Timer()


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

    max_wait = 60  # Wait for connect or fail
    while max_wait > 0:
        wlan.connect(ssid, password)
        time.sleep(3)
        if wlan.isconnected():
            break
        max_wait -= 1
        print(f"waiting for connection... retry countdown: {max_wait}")

    if wlan.status() != 3:  # Handle connection error
        raise RuntimeError(f"network connection failed, err: {wlan.status()}")
    else:
        wlan_ip, wlan_subnet_mask, wlan_gateway, wlan_dns_server = wlan.ifconfig()
        print(f"Connected, ip: {wlan_ip}")
        return wlan


def http_fan_on_off(req: str) -> None:
    global is_fan_on
    fan_on = req.find("fan=turn_on")
    fan_off = req.find("fan=turn_off")

    if not fan_on == -1 and not fan_off == -1:
        print(f"HTTP: Error, both buttons detected, REST request: fan=turn_on: {fan_on}, fan=turn_off: {fan_off}")
    elif not fan_off == -1:
        fan_pin.value(0)
        is_fan_on = False
        print(f"HTTP: Turning off Bentobox Fan. is_fan_on: {is_fan_on}")
    elif not fan_on == -1:
        fan_pin.value(1)
        is_fan_on = True
        print(f"HTTP: Turning on Bentobox Fan. is_fan_on: {is_fan_on}")
    else:
        print(f"HTTP: Incorrect REST request detected. REST request: fan=turn_on: {fan_on}, fan=turn_off: {fan_off}")


def read_adc() -> float:
    analog_value = adc_pin.read_u16()
    voltage = analog_value * (3.3 / 65535)
    return (4.75 + 10 + 10) / 4.75 * voltage


def debounce_handler(pin) -> None:
    global debounce_timer
    debounce_timer.init(mode=Timer.ONE_SHOT, period=1000, callback=button_pressed_handler)


def button_pressed_handler(pin) -> None:
    print("Button: pressed interrupt loop")
    global is_fan_on
    if not is_fan_on:
        fan_pin.value(1)
        is_fan_on = True
        print(f"Button: pressed, turning fan on. is_fan_on: {is_fan_on}")
    elif is_fan_on:
        fan_pin.value(0)
        is_fan_on = False
        print(f"Button: pressed, turning fan off. is_fan_on: {is_fan_on}")
    else:
        print(f"Button: pressed, but invalid is_fan_on value: {is_fan_on}")


button_pin.irq(trigger=Pin.IRQ_FALLING, handler=button_pressed_handler)  # upon boot up
wlan = wifi_setup(ssid, password)
addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
s = socket.socket()
s.bind(addr)
s.listen(1)
print("listening on", addr)

# serve http client
while True:
    try:
        cl, addr = s.accept()
        print("client connected from", addr)
        request = cl.recv(1024)
        request = request.decode()
        print(f"HTTP Request: {request}")
        req, *_ = request.split("\n")  # request REST

        http_fan_on_off(req)

        fan_state = "FAN set OFF" if fan_pin.value() == 0 else "FAN set ON"
        adc_reading = round(read_adc(), 3)

        # Create and send response
        stat_string = (
            f"{fan_state}<br>ADC feedback confirmation: Fan {'ON' if adc_reading < 3 else 'OFF'} ({adc_reading}V)"
        )
        response = html % stat_string
        cl.send("HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n")
        cl.send(response)
        cl.close()

    except OSError as e:
        cl.close()
        print("connection closed")
