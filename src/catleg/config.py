from dynaconf import Dynaconf  # type:ignore

settings = Dynaconf(
    envvar_prefix="CATLEG",
    settings_files=[".catleg.toml", ".catleg_secrets.toml"],
)

# `envvar_prefix` = export envvars with `export DYNACONF_FOO=bar`.
# `settings_files` = Load these files in the order.
