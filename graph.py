#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This module represents a variety of Graph problemes: min vertex cover, max clique and max cut.
It reads the problems from a text file that follows a certain structure to input the clauses,
and converts that input into a formula that a SAT solver is able to understand and solve.
"""

from __future__ import absolute_import, print_function

import argparse
import itertools
import os
import sys

import msat_runner
import wcnf


# Graph class
###############################################################################


class Graph:
    """This class represents an undirected graph. The graph nodes are
    labeled 1, ..., n, where n is the number of nodes, and the edges are
    stored as pairs of nodes.
    """

    def __init__(self, file_path=""):
        self.edges = []
        self.n_nodes = 0

        if file_path:
            self.read_file(file_path)

    def read_file(self, file_path):
        """Loads a graph from the given file.

        :param file_path: Path to the file that contains a graph definition.
        """
        with open(file_path, 'r') as stream:
            self.read_stream(stream)

    def read_stream(self, stream):
        """Loads a graph from the given stream.

        :param stream: A data stream from which read the graph definition.
        """
        n_edges = -1
        edges = set()

        reader = (l for l in (ll.strip() for ll in stream) if l)
        for line in reader:
            l = line.split()
            if l[0] == 'p':
                self.n_nodes = int(l[2])
                n_edges = int(l[3])
            elif l[0] == 'c':
                pass  # Ignore comments
            else:
                edges.add(frozenset([int(l[1]), int(l[2])]))

        self.edges = tuple(tuple(x) for x in edges)
        if n_edges != len(edges):
            print("Warning incorrect number of edges")

    def visualize(self, name="graph"):
        """Visualize graph using 'graphviz' library.

        To install graphviz you can use 'pip install graphviz'.
        Notice that graphviz should also be installed in your system.
        For ubuntu, you can install it using 'sudo apt install graphviz'
        :param name: Name of the generated file, defaults to "graph"
        :type name: str, optional
        :raises ImportError: When unable to import graphviz.
        """
        try:
            from graphviz import Graph
        except ImportError:
            msg = (
                "Could not import 'graphviz' module. "
                "Make shure 'graphviz' is installed "
                "or install it typing 'pip install graphviz'"
            )
            raise ImportError(msg)

        # Create graph
        dot = Graph()
        # Create nodes
        for n in range(1, self.n_nodes + 1):
            dot.node(str(n))
        # Create edges
        for n1, n2 in self.edges:
            dot.edge(str(n1), str(n2))
        # Visualize
        dot.render(name, view=True, cleanup=True)

    def min_vertex_cover(self, solver):
        """Computes the minimum vertex cover of the graph.

        :param solver: An instance of MaxSATRunner.
        :return: A solution (list of nodes).
        """
        # Instantiate the formula
        formula = wcnf.WCNFFormula()
        # Create variables
        nodes = [formula.new_var() for _ in range(self.n_nodes)]

        # Soft clauses
        for n in nodes:
            formula.add_clause([-n], weight=1)

        # Hard clauses
        for e1, e2 in self.edges:
            v1, v2 = nodes[e1 - 1], nodes[e2 - 1]
            formula.add_clause([v1, v2], weight=wcnf.TOP_WEIGHT)

        # Solve formula
        print("MVC", file=sys.stderr)
        print(formula, end="\n\n", file=sys.stderr)
        _, model = solver.solve(formula)

        # Translate model
        return [n for n in model if n > 0]

    def max_clique(self, solver):
        """Computes the maximum clique of the graph.

        :param solver: An instance of MaxSATRunner.
        :return: A solution (list of nodes).
        """
        # Instantiate the formula
        formula = wcnf.WCNFFormula()
        # Create variables
        nodes = [formula.new_var() for _ in range(self.n_nodes)]

        # Soft clauses
        for n in nodes:
            formula.add_clause([n], weight=1)

        # Hard clauses
        for v1, v2 in itertools.product(range(1, self.n_nodes + 1), range(1, self.n_nodes + 1)):

            # Load only those edges whose first coord is less than the second
            if (v1, v2) not in self.edges and (v2, v1) not in self.edges and v1 < v2:
                formula.add_clause([-v1, -v2], weight=wcnf.TOP_WEIGHT)

        # Solve formula
        print("MAX_CLIQUE", file=sys.stderr)
        print(formula, end="\n\n", file=sys.stderr)
        _, model = solver.solve(formula)

        # Translate model
        return [n for n in model if n > 0]

    def max_cut(self, solver):
        """Computes the maximum cut of the graph.

        :param solver: An instance of MaxSATRunner.
        :return: A solution (list of nodes).
        """
        # Instantiate the formula
        formula = wcnf.WCNFFormula()

        # Create variables
        nodes = [formula.new_var() for _ in range(self.n_nodes)]

        # Soft clauses
        for e1, e2 in self.edges:
            v1, v2 = nodes[e1 - 1], nodes[e2 - 1]
            formula.add_clause([v1, v2], weight=1)
            formula.add_clause([-v1, -v2], weight=1)

        # No hard clauses

        # Solve formula
        print("MAX_CUT", file=sys.stderr)
        print(formula, end="\n\n", file=sys.stderr)
        _, model = solver.solve(formula)

        # Translate model
        return [n for n in model if n > 0]


# Program main
###############################################################################


def main(argv=None):
    """
    Executes all the diferent graph problems and shows the result
    """
    args = parse_command_line_arguments(argv)

    solver = msat_runner.MaxSATRunner(args.solver)
    graph = Graph(args.graph)
    if args.visualize:
        graph.visualize(os.path.basename(args.graph))

    min_vertex_cover = graph.min_vertex_cover(solver)
    print("MVC", " ".join(map(str, min_vertex_cover)))

    max_clique = graph.max_clique(solver)
    print("MCLIQUE", " ".join(map(str, max_clique)))

    max_cut = graph.max_cut(solver)
    print("MCUT", " ".join(map(str, max_cut)))


# Utilities
###############################################################################


def parse_command_line_arguments(argv=None):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("solver", help="Path to the MaxSAT solver.")

    parser.add_argument("graph", help="Path to the file that descrives the"
                                      " input graph.")

    parser.add_argument("--visualize", "-v", action="store_true",
                        help="Visualize graph (graphviz required)")

    return parser.parse_args(args=argv)


# Entry point
###############################################################################


if __name__ == "__main__":
    sys.exit(main())
