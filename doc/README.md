# Kubernetes - MidoNet Integration Documentation

## Generating Documentation

The documentation is automatically generated in multiple formats from the
source in this directory thanks to
[Sphinx](https://pypi.python.org/pypi/Sphinx). To install sphinx using pip:

    $ pip install -U Sphinx

[Reno](https://pypi.python.org/pypi/reno/1.3.1) is a tool that creates the
Release Notes. It is also needed for the make command:

    $ pip install -U reno

To build the documenation in a specific format, e.g. html, simply do:

    $ make html

If you want to serve the documentation with an ad-hoc webserver, you can do:

    $ cd build/html && python -m SimpleHTTPServer 8080
