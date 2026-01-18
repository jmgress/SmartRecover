"""
Suppress deprecation warnings from third-party libraries.
This module should be imported as early as possible in the application.
"""
import warnings

# Suppress Python version deprecation warnings from Google libraries
warnings.filterwarnings("ignore", category=FutureWarning, module="google")
warnings.filterwarnings("ignore", category=FutureWarning, message=".*Python version.*")

# Suppress urllib3 OpenSSL warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="urllib3")
warnings.filterwarnings("ignore", message=".*urllib3.*OpenSSL.*")
warnings.filterwarnings("ignore", message=".*NotOpenSSLWarning.*")
