#!/usr/bin/env python3
"""
Demo script showcasing the logging and tracing capabilities of SmartRecover.

This script demonstrates:
1. Different log levels and their output
2. Tracing functionality with execution time
3. File logging capabilities
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def demo_log_levels():
    """Demonstrate different log levels."""
    print("\n" + "="*70)
    print("DEMO 1: Log Levels - INFO (Default)")
    print("="*70)
    
    os.environ['LOG_LEVEL'] = 'INFO'
    
    from backend.config import config_manager
    config_manager.reload()
    
    from backend.utils.logger import get_logger, LoggerManager
    LoggerManager.reset()
    LoggerManager.setup_logging()
    
    logger = get_logger("demo")
    
    logger.debug("🔍 This DEBUG message will NOT appear at INFO level")
    logger.info("ℹ️  This INFO message appears")
    logger.warning("⚠️  This WARNING message appears")
    logger.error("❌ This ERROR message appears")
    
    print("\n" + "="*70)
    print("DEMO 2: Log Levels - DEBUG")
    print("="*70)
    
    os.environ['LOG_LEVEL'] = 'DEBUG'
    config_manager.reload()
    LoggerManager.reset()
    LoggerManager.setup_logging()
    
    logger = get_logger("demo_debug")
    
    logger.debug("🔍 This DEBUG message NOW appears")
    logger.info("ℹ️  This INFO message appears")
    logger.warning("⚠️  This WARNING message appears")


def demo_tracing():
    """Demonstrate function tracing."""
    print("\n" + "="*70)
    print("DEMO 3: Function Tracing")
    print("="*70)
    
    os.environ['LOG_LEVEL'] = 'DEBUG'
    os.environ['ENABLE_TRACING'] = 'true'
    
    from backend.config import config_manager
    config_manager.reload()
    
    from backend.utils.logger import get_logger, LoggerManager, trace_execution
    LoggerManager.reset()
    LoggerManager.setup_logging()
    
    logger = get_logger("demo_tracing")
    
    @trace_execution
    def calculate_fibonacci(n):
        """Calculate fibonacci number (with tracing)."""
        logger.info(f"Calculating fibonacci({n})")
        if n <= 1:
            return n
        return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)
    
    result = calculate_fibonacci(5)
    logger.info(f"Result: {result}")


def demo_application_logging():
    """Demonstrate application-level logging."""
    print("\n" + "="*70)
    print("DEMO 4: Application Integration")
    print("="*70)
    
    os.environ['LOG_LEVEL'] = 'INFO'
    os.environ['ENABLE_TRACING'] = 'false'
    os.environ['OPENAI_API_KEY'] = 'demo-key'
    
    from backend.config import config_manager
    config_manager.reload()
    
    from backend.utils.logger import LoggerManager
    LoggerManager.reset()
    
    # Import main app to see initialization logs
    from backend.main import app
    
    print("\n✅ Application initialized - observe the startup logs above!")


def demo_production_config():
    """Show recommended production configuration."""
    print("\n" + "="*70)
    print("DEMO 5: Recommended Production Configuration")
    print("="*70)
    
    print("""
For production deployments, use:

config.yaml:
  logging:
    level: "INFO"              # Avoid DEBUG in production
    enable_tracing: false      # Never enable tracing in production
    log_file: "logs/app.log"   # Enable file logging

Or via environment variables:
  LOG_LEVEL=INFO
  ENABLE_TRACING=false
  LOG_FILE=/var/log/smartrecover/app.log

For development/debugging:
  LOG_LEVEL=DEBUG
  ENABLE_TRACING=true
  # No file logging needed, use console
    """)


def main():
    """Run all demos."""
    print("\n" + "="*70)
    print("SmartRecover Logging & Tracing Demo")
    print("="*70)
    
    try:
        demo_log_levels()
        demo_tracing()
        demo_application_logging()
        demo_production_config()
        
        print("\n" + "="*70)
        print("✅ Demo Complete!")
        print("="*70)
        print("\nKey Takeaways:")
        print("• Use INFO level for production, DEBUG for development")
        print("• Enable tracing only when debugging specific issues")
        print("• Configure file logging for production deployments")
        print("• Environment variables override config.yaml settings")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
