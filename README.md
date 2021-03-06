# SMTDoS

SMTDoS is a tool designed to find potential Denial-of-Service attacks
in given network topologies using an SMT-based approach.

## Getting Started

### Dependencies

Python 3 is recommended for running SMTDoS.

The application relies on the [Z3](http://z3prover.github.io) theorem prover.
In order to install Z3, follow the [instructions](https://github.com/Z3Prover/z3#python)
in the Github repository for the Python bindings.

[BRITE](https://www.cs.bu.edu/brite) is required for generating internet-like topologies.
Although it is no longer supported, a patched version can be obtained on
[Github](https://github.com/joelwanner/brite-patch).

Network attacks are visualized using [pydot](https://github.com/erocarrera/pydot),
a Python interface to Graphviz.

### Usage

No further installation is required upon cloning the repository and installing the required dependencies.

For a list of commands, use

```
python3 src/smtdos.py --help
```

### Benchmarking

Generate example network files for benchmarking and run them using the following commands:

```
python3 src/smtdos.py --generate crafted
python3 src/smtdos.py --generate random
python3 src/smtdos.py --benchmark examples
```

### Custom Topologies

To run the application on a custom topology, create a file that contains the topology description
and use the following command:

```
python3 src/smtdos.py -f [path-to-topology]
```

See examples for the structure of topology descriptions.

## Authors

* Joel Wanner – [Github](https://github.com/joelwanner)

Supervised by
* Prof. Dr. Adrian Perrig
* Samuel Hitz

## License

This project is licensed under the MIT License – see the [LICENSE.txt](LICENSE.txt) file for details.
Third-party licenses are included in the [LICENSES.txt](LICENSES.txt) file.
