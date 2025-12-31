# FlexClient Examples

This directory contains example scripts demonstrating how to use the FlexClient library to control FlexRadio 6K series radios.

## Prerequisites

1. **FlexRadio 6K Series Radio** - Connected to your network
2. **SmartLink Account** - Register at https://www.flexradio.com/smartlink/
3. **Radio Serial Number** - Find this in your radio's settings or SmartLink web interface

## Setup

### Install FlexClient

```bash
# From the project root
pip install -e .
```

### Configure Environment

Set your radio's serial number as an environment variable:

```bash
export FLEX_SERIAL_NUMBER="1234-5678-9012-3456"
```

Add this to your `~/.bashrc` or `~/.zshrc` to make it permanent.

## Examples

### 1. Basic Connection (`basic_connection.py`)

Demonstrates the fundamental connection workflow:
- Authenticating via SmartLink
- Connecting to your radio
- Subscribing to radio updates
- Reading current radio state

**Usage:**
```bash
python3 basic_connection.py
```

**What it does:**
- Connects to SmartLink using OAuth2 (opens browser for first-time login)
- Retrieves radio information
- Starts data receiver thread
- Subscribes to slice and panadapter updates
- Displays current radio state (frequency, mode, antennas, etc.)
- Properly disconnects

**Expected output:**
```
INFO - Connecting to SmartLink...
INFO - Using cached authentication tokens
INFO - Connecting to radio...
INFO - Successfully connected to radio
INFO - === Current Radio State ===
INFO - Available antennas: ['ANT1', 'ANT2', 'RX_A', 'XVTA']
INFO - Slice 0 Frequency: 14.100 MHz
INFO - Slice 0 Mode: USB
```

---

### 2. Audio Streaming (`audio_streaming.py`)

Demonstrates capturing audio from the radio:
- Creating an uncompressed audio stream
- Opening UDP connection for audio data
- Capturing samples for a specified duration
- Calculating capture statistics
- Writing audio to a file

**Usage:**
```bash
python3 audio_streaming.py
```

**What it does:**
- Tunes to 14.222 MHz in USB mode
- Creates an uncompressed audio stream
- Captures 10 seconds of audio data via UDP
- Reports capture statistics (samples, bytes, efficiency)
- Writes audio data to a file

**Expected output:**
```
INFO - Creating audio stream (uncompressed)...
INFO - Capturing audio for 10 seconds...
INFO - === Audio Capture Statistics ===
INFO - Received samples: 240000
INFO - Received bytes: 960000
INFO - Expected bytes: 960000
INFO - Capture efficiency: 100.0%
INFO - Audio data written to file
```

**Output files:**
- Audio data file (format depends on RxRemoteAudioStream implementation)

---

### 3. Panadapter Display (`panadapter_display.py`)

Demonstrates real-time spectrum visualization:
- Configuring the panadapter display
- Receiving spectrum data via UDP
- Creating an animated real-time plot
- Proper frequency and amplitude scaling

**Usage:**
```bash
python3 panadapter_display.py
```

**What it does:**
- Configures panadapter: 1000x700 pixels, ANT2, RF gain 0.9
- Opens UDP connection for spectrum data
- Creates animated matplotlib plot showing frequency vs amplitude
- Updates display at ~24 fps
- Shows frequency in MHz, amplitude in dBm

**Display:**
- X-axis: Frequency (MHz) centered on tuned frequency
- Y-axis: Signal amplitude (dBm)
- Real-time spectrum display similar to SDR# or HDSDR
- Close the plot window to exit

**Dependencies:**
```bash
pip install matplotlib numpy
```

---

### 4. Waterfall Display (`waterfall_display.py`)

Demonstrates real-time waterfall visualization:
- Configuring for waterfall data
- Receiving waterfall data via UDP
- Creating an animated waterfall plot
- Color-coded signal strength over time

**Usage:**
```bash
python3 waterfall_display.py
```

**What it does:**
- Configures panadapter for waterfall mode
- Opens UDP connection for waterfall data
- Creates animated matplotlib plot showing frequency vs time
- Updates display at ~24 fps
- Color represents signal strength (viridis colormap)

**Display:**
- X-axis: Frequency (MHz)
- Y-axis: Time (newest data at top)
- Color: Signal strength (darker = weaker, brighter = stronger)
- Close the plot window to exit

**Dependencies:**
```bash
pip install matplotlib
```

---

### 5. Configure Logging (`configure_logging.py`)

Demonstrates how to configure logging for the FlexClient library:
- Setting global log level
- Configuring module-specific log levels
- Custom log formatting

**Usage:**
```bash
python3 configure_logging.py
```

This is a reference script - import its configuration into your own code.

---

## Common Issues & Solutions

### Authentication

**Issue:** Browser doesn't open for login
- **Solution:** Make sure you have Firefox or Chrome installed
- **Alternative:** Specify browser: `SmartLink(browser="chrome")`

**Issue:** "No cached tokens" on every run
- **Solution:** Check keyring is properly installed: `pip install keyring`
- **Linux:** May need `python3-secretstorage` or `gnome-keyring`

### Connection

**Issue:** "Radio not found in authorized list"
- **Solution:**
  1. Verify serial number is correct
  2. Check radio is online and connected to SmartLink
  3. Verify your SmartLink account has access to this radio

**Issue:** "Connection Unsuccessful"
- **Solution:**
  1. Check radio is powered on and connected to network
  2. Verify SmartLink server is accessible
  3. Check firewall isn't blocking ports 4992 (TCP) and 4991 (UDP)

### Display Issues

**Issue:** Matplotlib plots don't appear
- **Solution:**
  - Ensure matplotlib backend is configured: `export MPLBACKEND=TkAgg`
  - Install GUI backend: `pip install PyQt5` or `pip install tkinter`

**Issue:** "No data in buffer" errors
- **Solution:** Increase sleep time before opening UDP connection (try 2-3 seconds)

### Performance

**Issue:** Laggy or slow display updates
- **Solution:**
  1. Reduce panadapter resolution: `Set(xpixels=500, ypixels=350)`
  2. Increase animation interval: `FuncAnimation(..., interval=100)`
  3. Close other applications using the radio

---

## Example Workflow

Here's a typical workflow for working with FlexRadio:

```python
import logging
from flexclient import Radio, SmartLink
from flexclient.DataHandler import ReceiveData

# 1. Configure logging
logging.basicConfig(level=logging.INFO)

# 2. Connect to SmartLink
smartlink = SmartLink()

# 3. Get your radio
radio_info = smartlink.GetRadioFromAvailable("YOUR-SERIAL-HERE")
radio = Radio(radio_info, smartlink)

# 4. Start data receiver
receiver = ReceiveData(radio)
receiver.start()

# 5. Subscribe to updates
radio.SendCommand("sub slice all")
radio.SendCommand("sub pan all")

# 6. Control the radio
slice = radio.GetSlice(0)
slice.Tune(14.222)  # MHz
slice.Set(mode="USB", rxant="ANT1")

# 7. Do your work
# ...

# 8. Clean up
receiver.running = False
radio.CloseRadio()
smartlink.CloseLink()
```

---

## Advanced Usage

### Multiple Radios

```python
smartlink = SmartLink()

# List all available radios
for radio_info in smartlink.radio_list:
    print(f"Serial: {radio_info['serial']}")
    print(f"IP: {radio_info['public_ip']}")

# Connect to specific radios
radio1_info = smartlink.GetRadioFromAvailable("1234-5678-9012-3456")
radio2_info = smartlink.GetRadioFromAvailable("6543-8765-2109-6543")

radio1 = Radio(radio1_info, smartlink)
radio2 = Radio(radio2_info, smartlink)
```

### Error Handling

```python
from flexclient import SmartLink
from flexclient.exceptions import (
    FlexClientError,
    AuthenticationError,
    RadioNotFoundError,
)

try:
    smartlink = SmartLink()
    radio_info = smartlink.GetRadioFromAvailable(serial)
    radio = Radio(radio_info, smartlink)
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
except RadioNotFoundError as e:
    print(f"Radio not found: {e}")
except FlexClientError as e:
    print(f"FlexClient error: {e}")
```

### Custom Logging

```python
import logging

# Configure different log levels for different modules
logging.getLogger("flexclient.SmartLink").setLevel(logging.DEBUG)
logging.getLogger("flexclient.Radio").setLevel(logging.INFO)
logging.getLogger("flexclient.DataHandler").setLevel(logging.WARNING)
```

---

## Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `FLEX_SERIAL_NUMBER` | Your radio's serial number | `1234-5678-9012-3456` |
| `MPLBACKEND` | Matplotlib display backend | `TkAgg`, `Qt5Agg` |

---

## Further Resources

- **FlexRadio Documentation:** https://www.flexradio.com/documentation/
- **SmartLink Setup:** https://www.flexradio.com/smartlink/
- **API Reference:** See source code docstrings
- **FlexClient Issues:** https://github.com/phase4ground/flexclient/issues

---

## Contributing

Found a bug or want to improve an example? Please submit an issue or pull request!

When reporting issues, please include:
- FlexClient version
- Radio model and firmware version
- Python version
- Operating system
- Complete error traceback
