#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para ejecutar tests de la REST API de forma independiente.
Útil para CI/CD y desarrollo local.
"""

import os
import sys
import subprocess
import argparse


def run_tests(test_module=None, verbose=False, coverage=False):
    """
    Ejecuta los tests del módulo REST API

    Args:
        test_module: Módulo específico a testear (ej: 'test_rest_api_auth')
        verbose: Salida verbose
        coverage: Ejecutar con coverage
    """

    # Configurar comando base
    cmd = ['python3', '-m', 'pytest']

    if verbose:
        cmd.extend(['-v', '--tb=short'])

    if coverage:
        cmd.extend(['--cov=controllers', '--cov-report=term-missing'])

    # Directorio de tests
    test_dir = os.path.dirname(os.path.abspath(__file__))

    if test_module:
        test_path = os.path.join(test_dir, f"{test_module}.py")
        if not os.path.exists(test_path):
            print(f"Error: Test module {test_module} not found")
            return 1
        cmd.append(test_path)
    else:
        cmd.append(test_dir)

    print(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, cwd=test_dir)
        return result.returncode
    except FileNotFoundError:
        print("Error: pytest not found. Install with: pip install pytest pytest-cov")
        return 1


def run_odoo_tests():
    """
    Ejecuta los tests usando el framework de testing de Odoo
    """
    print("Running Odoo framework tests...")

    # Comando para ejecutar tests específicos del módulo en Odoo
    cmd = [
        'python3', 'odoo-bin',
        '--test-enable',
        '--test-tags', 'rest_api_odoo',
        '--stop-after-init',
        '--log-level=test'
    ]

    try:
        result = subprocess.run(cmd)
        return result.returncode
    except FileNotFoundError:
        print("Error: odoo-bin not found. Make sure you're in the Odoo directory")
        return 1


def main():
    parser = argparse.ArgumentParser(description='Run REST API tests')
    parser.add_argument('--module', '-m', help='Specific test module to run')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--coverage', '-c', action='store_true', help='Run with coverage')
    parser.add_argument('--odoo', action='store_true', help='Use Odoo test framework')

    args = parser.parse_args()

    if args.odoo:
        return run_odoo_tests()
    else:
        return run_tests(args.module, args.verbose, args.coverage)


if __name__ == '__main__':
    sys.exit(main())