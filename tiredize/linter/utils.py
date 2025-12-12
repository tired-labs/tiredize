import typing


def get_config_int(config: typing.Dict[str, typing.Any], key) -> int:
    """
    Retrieve an integer configuration value.
    """
    raw_value = config.get(key)
    if isinstance(raw_value, int):
        return raw_value
    try:
        return int(raw_value)
    except:
        return -1


def get_config_str(config: typing.Dict[str, typing.Any], key) -> str:
    """
    Retrieve an string configuration value.
    """
    raw_value = config.get(key)
    if isinstance(raw_value, str):
        return raw_value
    try:
        return str(raw_value)
    except:
        return 0


def get_config_bool(config: typing.Dict[str, typing.Any], key) -> bool:
    """
    Retrieve an boolean configuration value.
    """
    raw_value = config.get(key)
    if isinstance(raw_value, bool):
        return raw_value
    try:
        return bool(raw_value)
    except:
        return False


def get_config_dict(config: typing.Dict[str, typing.Any], key) -> dict:
    """
    Retrieve an dictionary configuration value.
    """
    raw_value = config.get(key)
    if isinstance(raw_value, dict):
        return raw_value
    try:
        return dict(raw_value)
    except:
        return dict()


def get_config_list(config: typing.Dict[str, typing.Any], key) -> list:
    """
    Retrieve an list configuration value.
    """
    raw_value = config.get(key)
    if isinstance(raw_value, list):
        return raw_value
    try:
        return list(raw_value)
    except:
        return list()
