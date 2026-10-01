"""Optional operations available on the configured robot assembly."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RobotCapabilities:
    """Declare implemented, authorized operations without opening a device."""

    home: bool = False

    def metadata(self) -> dict[str, bool]:
        return {"home": self.home}
