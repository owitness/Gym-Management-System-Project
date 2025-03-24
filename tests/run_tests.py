import unittest
import sys
import os
import coverage
from coverage import Coverage
import logging
from datetime import datetime
import json
import subprocess
import time

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def setup_logging():
    """Set up logging configuration"""
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Create a timestamp for the log file name
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = f'logs/test_run_{timestamp}.log'

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Create a logger for test results
    logger = logging.getLogger('test_results')
    logger.setLevel(logging.INFO)

    return logger, log_file

def log_test_results(logger, result, coverage_data):
    """Log detailed test results"""
    # Log test summary
    logger.info("\n=== Test Summary ===")
    logger.info(f"Total Tests: {result.testsRun}")
    logger.info(f"Failures: {len(result.failures)}")
    logger.info(f"Errors: {len(result.errors)}")

    # Log failures
    if result.failures:
        logger.info("\n=== Test Failures ===")
        for failure in result.failures:
            logger.error(f"Test: {failure[0]}")
            logger.error(f"Error: {failure[1]}")

    # Log errors
    if result.errors:
        logger.info("\n=== Test Errors ===")
        for error in result.errors:
            logger.error(f"Test: {error[0]}")
            logger.error(f"Error: {error[1]}")

    # Log coverage data
    logger.info("\n=== Coverage Summary ===")
    logger.info(f"Total Coverage: {coverage_data['total_coverage']}%")
    logger.info(f"Lines Covered: {coverage_data['lines_covered']}")
    logger.info(f"Total Lines: {coverage_data['total_lines']}")

    # Log detailed coverage by module
    logger.info("\n=== Coverage by Module ===")
    for module, data in coverage_data['modules'].items():
        logger.info(f"\nModule: {module}")
        logger.info(f"Coverage: {data['coverage']}%")
        logger.info(f"Lines Covered: {data['lines_covered']}")
        logger.info(f"Total Lines: {data['total_lines']}")

def start_flask_server():
    """Start the Flask server in a separate process"""
    server_process = subprocess.Popen(
        ['python3', 'app.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    # Wait for server to start
    time.sleep(2)
    return server_process

def stop_flask_server(server_process):
    """Stop the Flask server process"""
    server_process.terminate()
    server_process.wait()

def run_tests():
    """Run all tests with coverage reporting and logging"""
    # Set up logging
    logger, log_file = setup_logging()
    logger.info("Starting test run...")

    # Start Flask server
    logger.info("Starting Flask server...")
    server_process = start_flask_server()

    try:
        # Start coverage measurement
        cov = Coverage()
        cov.start()
        logger.info("Started coverage measurement")

        # Discover and run all tests
        loader = unittest.TestLoader()
        start_dir = os.path.dirname(os.path.abspath(__file__))
        suite = loader.discover(start_dir, pattern='test_*.py')
        
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)

        # Stop coverage measurement
        cov.stop()
        cov.save()
        logger.info("Stopped coverage measurement")

        # Generate coverage data
        coverage_data = {
            'total_coverage': cov.report(),
            'lines_covered': cov.analysis2('app.py')[1],
            'total_lines': cov.analysis2('app.py')[2],
            'modules': {}
        }

        # Get coverage data for each module
        for module in cov.get_data().measured_files():
            analysis = cov.analysis2(module)
            coverage_data['modules'][module] = {
                'coverage': cov.report(module),
                'lines_covered': analysis[1],
                'total_lines': analysis[2]
            }

        # Log test results
        log_test_results(logger, result, coverage_data)

        # Generate HTML coverage report
        html_dir = 'coverage_html'
        cov.html_report(directory=html_dir)
        logger.info(f"HTML coverage report generated in {html_dir} directory")

        # Save coverage data to JSON file
        coverage_json = f'logs/coverage_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(coverage_json, 'w') as f:
            json.dump(coverage_data, f, indent=4)
        logger.info(f"Coverage data saved to {coverage_json}")

        # Log completion
        logger.info(f"\nTest run completed. Log file: {log_file}")
        logger.info(f"Coverage data: {coverage_json}")

        # Return 0 if tests passed, 1 if any failed
        return 0 if result.wasSuccessful() else 1

    finally:
        # Stop Flask server
        logger.info("Stopping Flask server...")
        stop_flask_server(server_process)

if __name__ == '__main__':
    sys.exit(run_tests()) 