import sounddevice as sd

# List all available devices
print("Available audio devices:")
devices = sd.query_devices()
for i, device in enumerate(devices):
    if(device['max_input_channels'] in [1]):
        print(f"{i}: {device['name']} - {device['max_input_channels']} input channels, {device['max_output_channels']} output channels")

print(sd.default.device)