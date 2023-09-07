# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

from subprocess import PIPE, Popen, run


project = "catleg"
copyright = "2023, the catala contributors"
author = "the catala contributors"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["myst_parser"]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

# version
pipe = Popen("hatch version", stdout=PIPE, shell=True)
version = pipe.stdout.read().decode("utf8")

# generate CLI reference
# (this command implies that `make html` is executed from the `docs`
# directory -- this could be made more robust?)
run(
    [
        "typer",
        "../src/catleg/catleg.py",
        "utils",
        "docs",
        "--name",
        "catleg",
        "--output",
        "cli_reference.md",
    ],
    check=True,
)
