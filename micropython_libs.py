"""
Introspect esp32 libraries.
"""
import esp
import esp32
import espnow
import network


print(f"{help(network)}")

print(f"{help(esp)}")
print(f"{esp.flash_size()=}")
print(f"{esp.flash_user_start()=}")

print(f"{help(esp32_libs)}")
print(f"{esp32_libs.mcu_temperature()=}")  # read the internal temperature of the MCU, in Celsius

print(f"{help(esp32_libs.PCNT)=}")

print(f"{help(esp32_libs.RMT)=}")

print(f"{help(espnow)=}")
print(f"{help(espnow.ESPNow)}")
