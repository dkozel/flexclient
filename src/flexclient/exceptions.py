"""FlexClient exception hierarchy."""


class FlexClientError(Exception):
    """Base exception for all flexclient errors."""

    pass


class ConnectionError(FlexClientError):
    """Network connection errors."""

    pass


class AuthenticationError(FlexClientError):
    """OAuth/authentication failures."""

    pass


class ProtocolError(FlexClientError):
    """FLEX protocol parsing errors."""

    pass


class RadioNotFoundError(FlexClientError):
    """Requested radio serial not in authorized list."""

    pass
