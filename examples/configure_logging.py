#!/usr/bin/env python3
"""Example: Configure logging for flexclient.

This example shows how to configure logging levels for the flexclient library.
"""

import logging

# Configure logging for the entire application
logging.basicConfig(
    level=logging.INFO,  # Set to DEBUG for more verbose output
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# You can also configure specific loggers for different modules
# For example, to see debug messages only from SmartLink:
# logging.getLogger('flexclient.SmartLink').setLevel(logging.DEBUG)

# Or to suppress verbose output from a specific module:
# logging.getLogger('flexclient.DataHandler').setLevel(logging.WARNING)

# The library will now use the configured logging instead of print statements
if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logger.info("Logging configured. FlexClient will use proper logging.")
    logger.info("Available log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL")
    logger.info("")
    logger.info("Example configurations:")
    logger.info("  - Set all to DEBUG: logging.basicConfig(level=logging.DEBUG)")
    logger.info(
        "  - SmartLink only: logging.getLogger('flexclient.SmartLink').setLevel(logging.DEBUG)"
    )
    logger.info(
        "  - Quiet DataHandler: logging.getLogger('flexclient.DataHandler').setLevel(logging.WARNING)"
    )
