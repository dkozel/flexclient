#!/usr/bin/env python3
"""Real-time Panadapter Display Example.

This example demonstrates:
- Configuring the panadapter display
- Opening UDP connection for spectrum data
- Creating an animated real-time spectrum plot
- Proper axis scaling with frequency and amplitude

The panadapter shows the frequency spectrum in real-time, similar to
a spectrum analyzer display.

Environment Variables:
    FLEX_SERIAL_NUMBER: Your radio's serial number (e.g., "1234-5678-9012-3456")

Dependencies:
    - matplotlib
    - numpy

Usage:
    export FLEX_SERIAL_NUMBER="1234-5678-9012-3456"
    python3 panadapter_display.py
"""

import logging
import os
import sys
from time import sleep

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

from flexclient import Radio, SmartLink
from flexclient.DataHandler import ReceiveData
from flexclient.exceptions import FlexClientError, RadioNotFoundError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global radio instance for animation callback
radio = None


def animate(frame):
    """Animation callback to update the panadapter plot.

    Args:
        frame: Frame number from FuncAnimation (unused)
    """
    try:
        plt.cla()

        # Get latest spectrum data
        data = radio.Panafall.PanBuffer.get_nowait()

        # Calculate frequency axis
        center = radio.Panafall.center
        bandwidth = radio.Panafall.bandwidth
        x_axis = np.linspace(
            center - (bandwidth / 2),
            center + (bandwidth / 2),
            len(data),
        )

        # Plot spectrum
        plt.xlim(x_axis[0], x_axis[-1])
        plt.ylim([radio.Panafall.min_dbm, radio.Panafall.max_dbm])
        plt.title("FlexRadio Panadapter Display")
        plt.xlabel("Frequency (MHz)")
        plt.ylabel("Amplitude (dBm)")
        plt.grid(True, alpha=0.3)
        plt.plot(x_axis, data, linewidth=1)

    except Exception as e:
        # Log errors but don't crash the animation
        logger.debug("Animation frame error: %s", e)


def main():
    """Display real-time panadapter from FlexRadio."""
    global radio

    serial = os.getenv("FLEX_SERIAL_NUMBER")
    if not serial:
        logger.error("FLEX_SERIAL_NUMBER environment variable not set")
        sys.exit(1)

    logger.info("FlexClient Panadapter Display Example")

    smartlink = None
    receive_thread = None

    try:
        # Connect to SmartLink and radio
        logger.info("Connecting to SmartLink...")
        smartlink = SmartLink(browser="firefox")

        logger.info("Retrieving radio information...")
        try:
            radio_info = smartlink.GetRadioFromAvailable(serial)
        except RadioNotFoundError:
            logger.error("Radio %s not found", serial)
            sys.exit(1)

        logger.info("Connecting to radio...")
        radio = Radio(radio_info, smartlink)

        if not radio.serverHandle:
            logger.error("Failed to connect to radio")
            sys.exit(1)

        # Start data receiver
        logger.info("Starting data receiver...")
        receive_thread = ReceiveData(radio)
        receive_thread.start()
        sleep(1)

        # Subscribe to updates
        logger.info("Subscribing to radio updates...")
        radio.UpdateAntList()
        radio.SendCommand("sub slice all")
        radio.GetSliceList()
        radio.SendCommand("sub pan all")
        sleep(1)

        # Configure receiver
        logger.info("Configuring receiver...")
        slice_0 = radio.GetSlice(0)
        slice_0.Tune(14.222)
        radio.SendCommand("slice t 0 14.222 autopan=1")
        slice_0.Set(mode="USB", rxant="ANT2")

        # Configure panadapter
        logger.info("Configuring panadapter...")
        radio.Panafall.Set(xpixels=1000)
        radio.Panafall.Set(ypixels=700)
        radio.Panafall.Set(rxant="ANT2")
        radio.Panafall.Set(rfgain=0.9)
        sleep(1)

        # Open UDP connection for spectrum data
        logger.info("Opening UDP connection...")
        radio.OpenUDPConnection()
        sleep(1)

        logger.info("Starting panadapter display...")
        logger.info("Close the plot window to exit")

        # Create animated plot
        # Update every 42ms (~24 fps)
        # Keep reference to animation to prevent garbage collection
        _ani = FuncAnimation(plt.gcf(), animate, interval=42, cache_frame_data=False)  # noqa: F841
        plt.tight_layout()
        plt.show()

        logger.info("Panadapter display closed")

    except FlexClientError as e:
        logger.error("FlexClient error: %s", e)
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error("Unexpected error: %s", e, exc_info=True)
        sys.exit(1)
    finally:
        # Clean up
        logger.info("Cleaning up...")
        if receive_thread:
            receive_thread.running = False
            receive_thread.join(timeout=2)
        if radio:
            if radio.UdpListening:
                radio.CloseUDPConnection()
            radio.CloseRadio()
        if smartlink:
            smartlink.CloseLink()
        logger.info("Cleanup complete")


if __name__ == "__main__":
    main()
