import typing


def get_config_int(
        config: typing.Dict[str, typing.Any],
        key: str
        ) -> int | None:
    """
    Retrieve an integer configuration value.
    """
    raw_value = config.get(key)
    if not isinstance(raw_value, int):
        return None
    return raw_value


def get_config_str(
        config: typing.Dict[str, typing.Any],
        key: str
        ) -> str | None:
    """
    Retrieve an string configuration value.
    """
    raw_value = config.get(key)
    if not isinstance(raw_value, str):
        return None
    return raw_value


def get_config_bool(
        config: typing.Dict[str, typing.Any],
        key: str
        ) -> bool | None:
    """
    Retrieve an boolean configuration value.
    """
    raw_value = config.get(key)
    if not isinstance(raw_value, bool):
        return None
    return raw_value


def get_config_dict(
        config: typing.Dict[str, typing.Any],
        key: str
        ) -> typing.Dict[str, typing.Any] | None:
    """
    Retrieve an dictionary configuration value.
    """
    raw_value: dict[str, typing.Any] | None = config.get(key)
    if not isinstance(raw_value, dict):
        return None
    return raw_value


def get_config_list(
        config: typing.Dict[str, typing.Any],
        key: str
        ) -> typing.List[str] | None:
    """
    Retrieve an list configuration value.
    """
    raw_value: list[str] | None = config.get(key)
    if not isinstance(raw_value, list):
        return None
    return raw_value
