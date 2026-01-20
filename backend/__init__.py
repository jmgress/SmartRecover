"""
Backend package for SmartRecover.
Warning suppression is initialized on package import.
"""

import warnings

# Suppress Python version deprecation warnings from Google libraries
warnings.filterwarnings("ignore", category=FutureWarning, module="google")
warnings.filterwarnings("ignore", category=FutureWarning, message=".*Python version.*")
warnings.filterwarnings("ignore", category=FutureWarning, message=".*end of life.*")

# Suppress urllib3 OpenSSL warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="urllib3")
warnings.filterwarnings("ignore", message=".*urllib3.*OpenSSL.*")
warnings.filterwarnings("ignore", message=".*NotOpenSSLWarning.*")
