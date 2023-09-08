.. _installation:

==============
 Installation
==============

``catleg`` is tested on Linux, macOS and Windows.

.. _installation_homebrew:


Using pip
=========

The `catleg package <https://pypi.org/project/catleg/>`__ can be installed using ``pip`` like so::

    pip install catleg

.. _installation_pipx:

Using pipx
==========

`pipx <https://pypi.org/project/pipx/>`__ is a tool for installing Python command-line applications in their own isolated environments. You can use ``pipx`` to install the ``catleg`` command-line tool like this::

    pipx install catleg

Providing Legifrance credentials
================================

``catleg`` uses the Legifrance API to access French legislative texts.

This API is authenticated and requires credentials, which may be obtained by registering on `the Piste portal <https://piste.gouv.fr/>`__.

To provide credentials to catleg, create a ``.catleg_secrets.toml`` file like so::

    lf_client_id = "your_client_id"
    lf_client_secret = "your_client_secret"

Alternatively, you may define the environment variables ``CATLEG_LF_CLIENT_ID`` and ``CATLEG_LF_CLIENT_SECRET``.

.. note::
   Legifrance authentication requires **oauth** credentials, not an API key.

