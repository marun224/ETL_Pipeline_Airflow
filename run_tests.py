#!/usr/bin/env python3
"""
Test runner script for the ETL Pipeline project.

This script provides a convenient way to run different types of tests
with proper environment setup and reporting.
"""

import sys
import os
import unittest
import argparse
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'dags'))


def discover_and_run_tests(test_dir, pattern='test_*.py', verbosity=2):
    """
    Discover and run tests in the specified directory.
    
    Args:
        test_dir: Directory to search for tests
        pattern: Pattern to match test files
        verbosity: Test output verbosity level
    
    Returns:
        TestResult object
    """
    loader = unittest.TestLoader()
    suite = loader.discover(test_dir, pattern=pattern)
    
    runner = unittest.TextTestRunner(
        verbosity=verbosity,
        buffer=True,
        failfast=False
    )
    
    return runner.run(suite)


def run_unit_tests(verbosity=2):
    """Run unit tests."""
    print("=" * 60)
    print("RUNNING UNIT TESTS")
    print("=" * 60)
    
    test_dir = project_root / 'tests' / 'unit'
    return discover_and_run_tests(str(test_dir), verbosity=verbosity)


def run_integration_tests(verbosity=2):
    """Run integration tests."""
    print("=" * 60)
    print("RUNNING INTEGRATION TESTS")
    print("=" * 60)
    
    test_dir = project_root / 'tests' / 'integration'
    return discover_and_run_tests(str(test_dir), verbosity=verbosity)


def run_all_tests(verbosity=2):
    """Run all tests."""
    print("=" * 60)
    print("RUNNING ALL TESTS")
    print("=" * 60)
    
    test_dir = project_root / 'tests'
    return discover_and_run_tests(str(test_dir), verbosity=verbosity)


def print_test_summary(result):
    """Print a summary of test results."""
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped) if hasattr(result, 'skipped') else 0
    
    print(f"Total tests run: {total_tests}")
    print(f"Successes: {total_tests - failures - errors - skipped}")
    print(f"Failures: {failures}")
    print(f"Errors: {errors}")
    print(f"Skipped: {skipped}")
    
    if failures > 0:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}")
    
    if errors > 0:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}")
    
    success_rate = ((total_tests - failures - errors) / total_tests * 100) if total_tests > 0 else 0
    print(f"\nSuccess rate: {success_rate:.1f}%")
    
    if failures == 0 and errors == 0:
        print("🎉 ALL TESTS PASSED!")
        return True
    else:
        print("❌ SOME TESTS FAILED!")
        return False


def main():
    """Main function to run tests based on command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run tests for the ETL Pipeline project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                    # Run all tests
  python run_tests.py --unit             # Run only unit tests
  python run_tests.py --integration      # Run only integration tests
  python run_tests.py --verbose          # Run with high verbosity
  python run_tests.py --quiet            # Run with minimal output
        """
    )
    
    parser.add_argument(
        '--unit', 
        action='store_true',
        help='Run only unit tests'
    )
    
    parser.add_argument(
        '--integration', 
        action='store_true',
        help='Run only integration tests'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Increase output verbosity'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Decrease output verbosity'
    )
    
    args = parser.parse_args()
    
    # Determine verbosity level
    if args.quiet:
        verbosity = 0
    elif args.verbose:
        verbosity = 2
    else:
        verbosity = 1
    
    # Run appropriate tests
    if args.unit and args.integration:
        print("Error: Cannot specify both --unit and --integration")
        sys.exit(1)
    elif args.unit:
        result = run_unit_tests(verbosity)
    elif args.integration:
        result = run_integration_tests(verbosity)
    else:
        result = run_all_tests(verbosity)
    
    # Print summary and exit with appropriate code
    success = print_test_summary(result)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()