#!/usr/bin/env python3
"""Audio Streaming Example.

This example demonstrates:
- Creating an uncompressed audio stream
- Opening UDP connection for audio data
- Capturing audio samples for a specified duration
- Calculating received data metrics
- Writing audio data to a file

Environment Variables:
    FLEX_SERIAL_NUMBER: Your radio's serial number (e.g., "1234-5678-9012-3456")

Usage:
    export FLEX_SERIAL_NUMBER="1234-5678-9012-3456"
    python3 audio_streaming.py
"""

import logging
import os
import sys
from time import sleep

from flexclient import Radio, SmartLink
from flexclient.DataHandler import ReceiveData
from flexclient.exceptions import FlexClientError, RadioNotFoundError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Audio stream parameters
TEST_DURATION = 10  # seconds
SAMPLE_RATE = 24000  # Hz
BYTES_PER_SAMPLE = 4  # 32-bit float


def main():
    """Demonstrate audio streaming from FlexRadio."""
    serial = os.getenv("FLEX_SERIAL_NUMBER")
    if not serial:
        logger.error("FLEX_SERIAL_NUMBER environment variable not set")
        sys.exit(1)

    logger.info("FlexClient Audio Streaming Example")
    logger.info("Duration: %d seconds", TEST_DURATION)

    smartlink = None
    radio = None
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

        # Configure slice for listening
        logger.info("Configuring receiver...")
        slice_0 = radio.GetSlice(0)
        slice_0.Tune(14.222)  # Tune to 14.222 MHz
        radio.SendCommand("slice t 0 14.222 autopan=1")
        slice_0.Set(mode="USB", rxant="ANT2")
        sleep(1)

        # Create audio stream (uncompressed)
        logger.info("Creating audio stream (uncompressed)...")
        radio.CreateAudioStream(isCompressed=False)
        sleep(1)

        if not radio.RxAudioStreamer:
            logger.error("Failed to create audio stream")
            sys.exit(1)

        logger.info("Audio stream created successfully")

        # Open UDP connection
        logger.info("Opening UDP connection...")
        radio.OpenUDPConnection()
        sleep(1)

        # Capture audio data
        logger.info("Capturing audio for %d seconds...", TEST_DURATION)
        sleep(TEST_DURATION)

        # Close UDP connection
        logger.info("Stopping audio capture...")
        radio.CloseUDPConnection()

        # Calculate statistics
        if radio.RxAudioStreamer:
            received_samples = radio.RxAudioStreamer.outBuffer.qsize()
            received_bytes = received_samples * BYTES_PER_SAMPLE
            expected_bytes = TEST_DURATION * SAMPLE_RATE * BYTES_PER_SAMPLE

            logger.info("=== Audio Capture Statistics ===")
            logger.info("Received samples: %d", received_samples)
            logger.info("Received bytes: %d", received_bytes)
            logger.info("Expected bytes: %d", expected_bytes)
            logger.info(
                "Capture efficiency: %.1f%%",
                (received_bytes / expected_bytes * 100) if expected_bytes > 0 else 0,
            )

            # Write to file
            logger.info("Writing audio data to file...")
            radio.RxAudioStreamer.WriteToFile()
            logger.info("Audio data written successfully")
        else:
            logger.warning("No audio streamer available")

        logger.info("Audio streaming example completed")

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
