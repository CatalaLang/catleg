
from dynaconf import Dynaconf

settings = Dynaconf(
    envvar_prefix="CATDEV",
    settings_files=['.catdev.toml', '.catdev_secrets.toml'],
)

# `envvar_prefix` = export envvars with `export DYNACONF_FOO=bar`.
# `settings_files` = Load these files in the order.
