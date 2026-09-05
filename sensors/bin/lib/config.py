from dynaconf import Dynaconf

settings = Dynaconf(
    settings_files=['/app/sensors-config-default.toml','/app/sensors/sensors-config.toml'],
    envvar_prefix="SENSORS"
)