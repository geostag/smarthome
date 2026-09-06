from dynaconf import Dynaconf

settings = Dynaconf(
    settings_files=['/app/sensors-config-default.toml','/app/sensors-config.toml'],
    #settings_files=['sensors/sensors-config-default.toml','./sensors-config.toml'],
    envvar_prefix="SENSORS"
)