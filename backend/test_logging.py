#!/usr/bin/env python3
"""
Test script to demonstrate the logging and tracing capabilities of SmartRecover.

This script tests:
1. Basic logging functionality
2. Different log levels
3. Tracing decorators
4. Configuration loading
5. File logging
"""

import os
import sys
import tempfile
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_basic_logging():
    """Test basic logging functionality."""
    print("\n" + "=" * 60)
    print("Test 1: Basic Logging")
    print("=" * 60)

    from backend.utils.logger import LoggerManager, get_logger

    LoggerManager.setup_logging()
    logger = get_logger("test_basic")

    logger.debug("This is a DEBUG message")
    logger.info("This is an INFO message")
    logger.warning("This is a WARNING message")
    logger.error("This is an ERROR message")

    print("✅ Basic logging test passed")
    return True


def test_log_levels():
    """Test different log levels."""
    print("\n" + "=" * 60)
    print("Test 2: Log Levels")
    print("=" * 60)

    # Test with DEBUG level
    os.environ["LOG_LEVEL"] = "DEBUG"

    from backend.config import config_manager

    config_manager.reload()

    from backend.utils.logger import LoggerManager, get_logger

    LoggerManager.reset()  # Reset to reinitialize with new config
    LoggerManager.setup_logging()

    logger = get_logger("test_levels")
    logger.debug("DEBUG level is now visible")
    logger.info("INFO level message")

    # Test with WARNING level
    print("\nChanging to WARNING level...")
    os.environ["LOG_LEVEL"] = "WARNING"
    config_manager.reload()
    LoggerManager.reset()
    LoggerManager.setup_logging()

    logger = get_logger("test_levels_2")
    logger.info("This INFO message should NOT appear")
    logger.warning("This WARNING message SHOULD appear")

    print("✅ Log levels test passed")
    return True


def test_tracing():
    """Test tracing functionality."""
    print("\n" + "=" * 60)
    print("Test 3: Function Tracing")
    print("=" * 60)

    os.environ["LOG_LEVEL"] = "DEBUG"
    os.environ["ENABLE_TRACING"] = "true"

    from backend.config import config_manager

    config_manager.reload()

    from backend.utils.logger import LoggerManager, get_logger, trace_execution

    LoggerManager.reset()
    LoggerManager.setup_logging()

    logger = get_logger("test_tracing")

    @trace_execution
    def sample_function(x, y):
        """Sample function to test tracing."""
        logger.info(f"Computing {x} + {y}")
        return x + y

    result = sample_function(5, 10)
    assert result == 15, f"Expected 15, got {result}"

    print("✅ Tracing test passed")
    return True


def test_configuration():
    """Test configuration loading."""
    print("\n" + "=" * 60)
    print("Test 4: Configuration Loading")
    print("=" * 60)

    from backend.config import get_config

    config = get_config()
    print(f"LLM Provider: {config.llm.provider}")
    print(f"Log Level: {config.logging.level}")
    print(f"Enable Tracing: {config.logging.enable_tracing}")
    print(f"Log Format: {config.logging.format[:50]}...")

    print("✅ Configuration test passed")
    return True


def test_file_logging():
    """Test file logging."""
    print("\n" + "=" * 60)
    print("Test 5: File Logging")
    print("=" * 60)

    # Create temp log file
    temp_log = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".log")
    temp_log_path = temp_log.name
    temp_log.close()

    os.environ["LOG_FILE"] = temp_log_path
    os.environ["LOG_LEVEL"] = "INFO"
    os.environ["ENABLE_TRACING"] = "false"

    from backend.config import config_manager

    config_manager.reload()

    from backend.utils.logger import LoggerManager, get_logger

    LoggerManager.reset()
    LoggerManager.setup_logging()

    logger = get_logger("test_file")
    logger.info("Test message for file logging")
    logger.warning("Warning message for file logging")

    # Check file contents
    with open(temp_log_path) as f:
        contents = f.read()
        assert "Test message for file logging" in contents
        assert "Warning message for file logging" in contents

    # Clean up
    os.unlink(temp_log_path)

    print(f"✅ File logging test passed (logged to {temp_log_path})")
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("SmartRecover Logging System Test Suite")
    print("=" * 60)

    tests = [
        test_basic_logging,
        test_log_levels,
        test_tracing,
        test_configuration,
        test_file_logging,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_func.__name__} failed: {e}")
            import traceback

            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)

    if failed == 0:
        print("\n✅ All tests passed!")
        return 0
    else:
        print(f"\n❌ {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
