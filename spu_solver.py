#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This module represents the problem of the software package upgrades,
in which we have packages to be installed, with dependencies and conflicts in some of them.
Our objective is to maximize the number of packages installed
"""

import argparse
import sys

import msat_runner
import wcnf


class SPU:
    """
    This class represents the problem itself,
    with its important attributes and the functions to solve it
    """

    def __init__(self, solver=None):
        self.packages = {}
        self.package_ids = {}
        self.num_packages = 0
        self.formula = wcnf.WCNFFormula()
        self.solver = solver

        # To validate
        self.dependencies = {}
        self.conflicts = {}

    def generate_formula_and_solve(self, file_path):
        """
        Checks if the file path passed is correct and opens it to parse it
        """
        if file_path:
            with open(file_path, 'r', encoding="utf8") as stream:
                return self.parse_and_solve(stream)
        raise FileNotFoundError

    def parse_and_solve(self, stream):
        """
        Discenrns between the different types of input lines (dependencies, conflicts, ...) and
        manages each o
        """
        reader = (line for line in (lineline.strip() for lineline in stream) if line)
        for line in reader:
            line = line.split()

            if line[0] == 'p':
                self.num_packages = int(line[2])

            elif line[0] == 'n':
                self.manage_package(line[1])

            elif line[0] == 'd':
                self.manage_dependency(line[1:])

            elif line[0] == 'c':
                self.manage_conflict(line[1:])

            else:  # If there's a hashtag or any other invalid character, ignore it
                pass

        # Makes sure that the number of packages told to us in the first line
        # is the same as the number of packages declared further in the file
        if len(self.packages) != self.num_packages:
            print("Nombre de paquets incorrecte...")
            sys.exit(1)

        # Solve formula
        solution = self.solver.solve(self.formula)
        return solution

    def manage_package(self, package):
        """
        Parse the declaration of the packages and add its clauses
        """
        package_id = len(self.packages) + 1
        self.packages[package] = package_id
        self.package_ids[package_id] = package
        self.formula.new_var()  # Package 1 == Var 1 of the formula13
        self.formula.add_clause([self.packages[package]], weight=1)

        # To validate
        self.dependencies[package] = []
        self.conflicts[package] = []

    def manage_dependency(self, dependencies):
        """
        Parse the declaration of the dependencies and add its clauses
        """
        self.check_package(dependencies[0])
        new_clause = []
        for dependency in dependencies[1:]:
            self.check_package(dependencies[1])
            new_clause += [self.packages[dependency]]

        self.dependencies[dependencies[0]] += [dependencies[1:]]
        dependent = self.packages[dependencies[0]]
        self.formula.add_clause([-dependent] + new_clause, weight=wcnf.TOP_WEIGHT)

    def manage_conflict(self, conflicts):
        """
        Parse the declaration of the conflicts and add its clauses
        """
        self.check_package(conflicts[1])
        conflictable = self.packages[conflicts[0]]
        conflict = self.packages[conflicts[1]]
        self.formula.add_clause([-conflictable] + [-conflict], weight=wcnf.TOP_WEIGHT)

        # To validate
        self.conflicts[conflicts[0]] = self.conflicts[conflicts[0]] + [conflicts[1]]

    def check_package(self, package):
        """
        Checks whether a certain package has been delcared
        """
        if self.packages.get(package) is None:
            print("El paquet no ha estat declarat...")
            sys.exit(2)

    def print_solution(self, solution):
        """
        Prints the packages that connot be installed,
        by alfabetical order and with a space between them
        """
        # Get packages that can't be installed
        opt, model = solution
        installed_packages = []
        print("o " + str(opt))
        print("v", end="")
        for package in model:
            if package < 0:
                installed_packages += [self.package_ids[abs(package)]]

        # Sort packages that can't be installed by alfabetical order
        installed_packages.sort()

        # Print packages
        for package in installed_packages:
            print(" " + package, end="")
        print()

    def check_solution(self, solution):
        """
        Checks the solution if the "--validate" option has been called
        """
        _, model = solution
        correct = True
        for package in model:
            if package > 0:
                if not self.ok_dependencies(package, model) or \
                        not self.ok_conflicts(package, model):
                    correct = False
                    break
        if correct:
            print("c VALIDATION OK")
        else:
            print("c VALIDATION WRONG")

    def ok_dependencies(self, package, model):
        """
        Checks if the dependencies of the solution are satisfied
        """
        sat_dependencies = 0
        if self.dependencies.get(package) is None:
            return True
        for dependance in self.dependencies[package]:
            for item in dependance:
                if item in model and item > 0:
                    sat_dependencies += 1
                    break
        return sat_dependencies == len(self.dependencies[package])

    def ok_conflicts(self, package, model):
        """
        Checks if the conflicts of the solution are satisfied
        """
        if self.conflicts.get(package) is not None:
            for conflict in self.conflicts[package]:
                if conflict in model and conflict > 0:
                    return False
        return True


def main(argv=None):
    """
    Craetes an object that represents the problem,
    then solve it and print it's solution.
    Also, if the "--validate" option has been called, validate the answer
    """
    args = parse_args(argv)
    solver = msat_runner.MaxSATRunner(args.solver)

    spu_problem = SPU(solver)
    solution = spu_problem.generate_formula_and_solve(args.problem)
    spu_problem.print_solution(solution)
    if args.validate:
        spu_problem.check_solution(solution)


def parse_args(argv=None):
    """
    Parse the arguments
    """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("solver", help="Path to the MaxSAT solver.")

    parser.add_argument("problem", help="Path to the problem instance.")

    parser.add_argument("--validate", action="store_true",
                        help="Specify if the user wants to check the solution.")

    return parser.parse_args(args=argv)


if __name__ == '__main__':
    sys.exit(main())
