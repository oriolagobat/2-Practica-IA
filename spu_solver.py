#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import sys

import msat_runner
import wcnf


class SPU(object):
    def __init__(self, file_path="", solver=None):
        self.packages = {}
        self.package_ids = {}
        self.num_packages = 0
        self.file_path = file_path
        self.formula = wcnf.WCNFFormula()
        self.solver = solver
        self.dependencies = {}
        self.conflicts = {}

    def generate_formula_and_solve(self):
        if self.file_path:
            with open(self.file_path, 'r') as stream:
                return self.read_stream(stream)

    def read_stream(self, stream):
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

            else:  # Si # o qualsvol altra merda
                pass

        print(self.formula, file=sys.stderr)
        print("Dependencies")
        print(self.dependencies)
        print("Conflicts")
        print(self.conflicts)

        if len(self.packages) != self.num_packages:  # AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA FER UN TEST PER COMPROBAR AIXÒ AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
            print("Nombre de paquets incorrecte...")
            sys.exit(1)

        # Solve formula
        solution = self.solver.solve(self.formula)
        return solution

    def manage_package(self, package):
        package_id = len(self.packages) + 1
        self.packages[package] = package_id
        self.package_ids[package_id] = package
        self.formula.new_var()  # Paquet 1 = variable "1" de la formula, ....
        self.formula.add_clause([self.packages[package]], weight=1)

        # To help validate
        self.dependencies[package] = []
        self.conflicts[package] = []

    def manage_dependency(self, dependencies):
        self.check_package(dependencies[0])
        new_clause = []
        for dependency in dependencies[1:]:
            self.check_package(dependencies[1])
            new_clause += [self.packages[dependency]]

            # To valdiate
            self.dependencies[dependencies[0]] = self.dependencies[dependencies[0]] + [dependency]
        dependent = self.packages[dependencies[0]]
        self.formula.add_clause([-dependent] + new_clause, weight=wcnf.TOP_WEIGHT)

    def manage_conflict(self, conflicts):
        self.check_package(conflicts[1])
        conflictable = self.packages[conflicts[0]]
        conflict = self.packages[conflicts[1]]
        self.formula.add_clause([-conflictable] + [-conflict], weight=wcnf.TOP_WEIGHT)

        # To validate
        self.conflicts[conflicts[0]] = self.conflicts[conflicts[0]] + [conflicts[1]]

    def check_package(self, package):
        if self.packages.get(package) is None:
            print("El paquet no ha estat declarat...")
            sys.exit(2)

    def print_solution(self,
                       solution):  # AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA ALFABETIC AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
        opt, model = solution
        print("o " + str(opt))
        print("v", end="")
        for package in model:
            if package < 0:
                print(" " + self.package_ids[abs(package)], end="")
        print()

    def check_solution(self, solution):
        _, model = solution
        ok = True
        for package in model:
            if package > 0:
                if not self.ok_dependencies(package, model) or not self.ok_conflicts(package, model):
                    ok = False
                    break
        if ok:
            print("c VALIDATION OK")
        else:
            print("c VALIDATION WRONG")

    # AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA AQUEST ES ELQ UE FALTE ARREGALR AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA

    def ok_dependencies(self, package, model):
        for pkg in model:
            print(pkg)
            if pkg > 0:
                pkg = self.package_ids[pkg]
                if pkg in self.dependencies[self.package_ids[package]]:
                    return True
        return False

    def ok_conflicts(self, package, model):
        for pkg in model:
            print(pkg)
            if pkg > 0:
                pkg = self.package_ids[pkg]
                if pkg in self.conflicts[self.package_ids[package]]:
                    return False
        return True


def main(argv=None):
    args = parse_args(argv)
    solver = msat_runner.MaxSATRunner(args.solver)

    spu_problem = SPU(args.problem, solver)
    solution = spu_problem.generate_formula_and_solve()
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

    parser.add_argument("--validate", action="store_true", help="Specify if the user wants to check the solution.")

    return parser.parse_args(args=argv)


if __name__ == '__main__':
    sys.exit(main())

# AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA  passar pylint AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
