import sounddevice as sd

def list_input_devices():
    devices = sd.query_devices()
    for i, dev in enumerate(devices):
        if dev['max_input_channels'] > 0:
            print(f"ID {i}: {dev['name']}")

list_input_devices()