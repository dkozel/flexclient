#!/usr/bin/env python3
"""Basic FlexRadio Connection Example.

This example demonstrates:
- Connecting to a FlexRadio via SmartLink
- Authenticating with OAuth2
- Starting the data receiver thread
- Subscribing to slice and panadapter updates
- Reading current radio state
- Properly closing connections

Environment Variables:
    FLEX_SERIAL_NUMBER: Your radio's serial number (e.g., "1234-5678-9012-3456")

Usage:
    export FLEX_SERIAL_NUMBER="1234-5678-9012-3456"
    python3 basic_connection.py
"""

import argparse
import logging
import os
import sys
from time import sleep

# Import from the public API
from flexclient import Radio, SmartLink
from flexclient.DataHandler import ReceiveData
from flexclient.exceptions import FlexClientError, RadioNotFoundError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    """Connect to radio and demonstrate basic operations."""
    parser = argparse.ArgumentParser(description="Basic FlexRadio connection example")
    parser.add_argument(
        "--serial", help="Radio serial number (overrides FLEX_SERIAL_NUMBER env)"
    )
    args = parser.parse_args()

    logger.info("FlexClient Basic Connection Example")

    # Create SmartLink early so we can use the first available radio if needed
    smartlink = None
    radio = None
    receive_thread = None

    try:
        logger.info("Connecting to SmartLink...")
        smartlink = SmartLink(browser="firefox")

        if args.serial:
            serial = args.serial
        else:
            serial = os.getenv("FLEX_SERIAL_NUMBER")
            if not serial:
                if smartlink.radio_list and len(smartlink.radio_list) > 0:
                    serial = smartlink.radio_list[0].get("serial")
                    logger.info(
                        "No serial specified; using first available radio: %s", serial
                    )
                else:
                    logger.error(
                        "No serial specified and no radios available from SmartLink"
                    )
                    logger.info("Set FLEX_SERIAL_NUMBER or provide --serial")
                    sys.exit(1)

        logger.info("Serial Number: %s", serial)

        # Get radio information
        logger.info("Retrieving radio information...")
        try:
            radio_info = smartlink.GetRadioFromAvailable(serial)
        except (RadioNotFoundError, ValueError):
            logger.error("Radio %s not found in authorized list", serial)
            logger.info("Available radios: %s", smartlink.radio_list)
            sys.exit(1)

        logger.info("Radio found: %s at %s", serial, radio_info.get("public_ip"))

        # Connect to radio
        logger.info("Connecting to radio...")
        radio = Radio(radio_info, smartlink)

        if not radio.serverHandle:
            logger.error("Failed to connect to radio - no server handle received")
            sys.exit(1)

        logger.info("Successfully connected to radio")

        # Start data receiver thread
        logger.info("Starting data receiver thread...")
        receive_thread = ReceiveData(radio)
        receive_thread.start()

        # Allow time for initial data
        sleep(1)

        # Subscribe to updates
        logger.info("Subscribing to radio updates...")
        radio.UpdateAntList()
        radio.SendCommand("sub slice all")
        radio.GetSliceList()
        radio.SendCommand("sub pan all")

        # Wait for subscriptions to populate data
        sleep(1)

        # Display current radio state
        logger.info("=== Current Radio State ===")
        logger.info("Available antennas: %s", radio.AntList)

        if radio.SliceList:
            slice_0 = radio.GetSlice(0)
            logger.info("Slice 0 Frequency: %.3f MHz", slice_0.RF_frequency)
            logger.info("Slice 0 Mode: %s", slice_0.mode)
            logger.info("Slice 0 Antenna: %s", slice_0.rxant)

        if radio.Panafall:
            logger.info("Panadapter Center: %.3f MHz", radio.Panafall.center)
            logger.info("Panadapter Bandwidth: %.3f MHz", radio.Panafall.bandwidth)
            logger.info(
                "Panadapter Size: %dx%d",
                radio.Panafall.x_pixels,
                radio.Panafall.y_pixels,
            )

        logger.info("=========================")

        # Keep connection alive for a bit
        logger.info("Monitoring radio state for 5 seconds...")
        sleep(5)

        logger.info("Example completed successfully")

    except FlexClientError as e:
        logger.error("FlexClient error: %s", e)
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error("Unexpected error: %s", e, exc_info=True)
        sys.exit(1)
    finally:
        # Clean up resources
        logger.info("Cleaning up...")
        if receive_thread:
            receive_thread.running = False
            receive_thread.join(timeout=2)
        if radio:
            radio.CloseRadio()
        if smartlink:
            smartlink.CloseLink()
        logger.info("Cleanup complete")


if __name__ == "__main__":
    main()
