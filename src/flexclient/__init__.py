"""FlexClient - Python client for FlexRadio 6K series radios."""

__version__ = "0.1.0"

# Public API
from .exceptions import (
    AuthenticationError,
    ConnectionError,
    FlexClientError,
    ProtocolError,
    RadioNotFoundError,
)
from .Panafall import Panafall
from .Radio import Radio
from .RxRemoteAudioStream import RxRemoteAudioStream
from .Slice import Slice
from .SmartLink import SmartLink

__all__ = [
    "Radio",
    "SmartLink",
    "Slice",
    "Panafall",
    "RxRemoteAudioStream",
    "FlexClientError",
    "ConnectionError",
    "AuthenticationError",
    "ProtocolError",
    "RadioNotFoundError",
]
