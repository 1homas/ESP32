import machine, time


class ESP32C6_User_LED():
    """
    Utility functions for the User LED.
    """

    ESP32C6_USER_LED_PIN = 15
    DURATION = 100  # time, in milliseconds, to be on/off
    PINS_MAX = 40  # pin range; 0 to PINS_MAX
    CYCLES = 20  # number of iterations
    led = None

    # def __new__(cls):
    #     print(f"__new__()")
    #     return super.__new__(cls)

    def __init__(self, test:str="Default"):
        print(f"__init__({test})")

        self.led = machine.Signal(
            machine.Pin(self.ESP32C6_USER_LED_PIN, machine.Pin.OUT), invert=True
        )

    def on(self):
        """LED on."""
        print(f"on()")
        self.led.on()  # Turn LED on

    def off(self):
        """LED off."""
        print(f"off()")
        self.led.off()  # Turn LED on

    def cycle(self, cycles:int=1, ms:int=DURATION):
        """Cycle the LED on and off for the specified number of cycles and duration, in milliseconds."""
        for n in range(0, cycles):
            self.led.on()
            print(f"ON")
            time.sleep_ms(ms)

            self.led.off()
            print(f"OFF")
            time.sleep_ms(ms)

    def bounce(self, ms:int=DURATION):
            """Bounce the LED on and off once."""
            self.led.on()
            print(f"ON")
            time.sleep_ms(ms)

            self.led.off()
            print(f"OFF")
            time.sleep_ms(ms)

    def clear(self):
        """Same as off."""
        self.off()


def main():
    print(f"main()")

    led = ESP32C6_User_LED()
    led.on()
    led.off()
    led.cycle()
    led.cycle(5,200)
    led.bounce()
    led.bounce(2000)

if __name__ == "__main__":
    main()
