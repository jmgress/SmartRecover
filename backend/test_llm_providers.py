#!/usr/bin/env python3
"""
Test script to demonstrate LLM provider configuration.

This script shows how the SmartRecover system can be configured to use different LLM providers:
- OpenAI
- Google Gemini
- Ollama (local)

Usage:
    python test_llm_providers.py [provider]
    
    provider: openai, gemini, or ollama (default: ollama)
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_provider(provider_name: str):
    """Test a specific LLM provider."""
    print(f"\n{'='*60}")
    print(f"Testing LLM Provider: {provider_name.upper()}")
    print('='*60)
    
    # Set the provider via environment variable
    os.environ['LLM_PROVIDER'] = provider_name
    
    # For testing purposes, set mock API keys if not present
    if provider_name == 'openai' and not os.getenv('OPENAI_API_KEY'):
        print("⚠️  No OPENAI_API_KEY found. Set a valid key to test OpenAI.")
        os.environ['OPENAI_API_KEY'] = 'sk-test-key'
    
    if provider_name == 'gemini' and not os.getenv('GOOGLE_API_KEY'):
        print("⚠️  No GOOGLE_API_KEY found. Set a valid key to test Gemini.")
        os.environ['GOOGLE_API_KEY'] = 'test-key'
    
    try:
        # Import after setting environment
        from backend.llm.llm_manager import LLMManager
        from backend.config import get_config
        
        # Get configuration
        config = get_config()
        print(f"\n📋 Configuration:")
        print(f"   Provider: {config.llm.provider}")
        
        if provider_name == 'openai':
            print(f"   Model: {config.llm.openai.model}")
            print(f"   Temperature: {config.llm.openai.temperature}")
        elif provider_name == 'gemini':
            print(f"   Model: {config.llm.gemini.model}")
            print(f"   Temperature: {config.llm.gemini.temperature}")
        elif provider_name == 'ollama':
            print(f"   Model: {config.llm.ollama.model}")
            print(f"   Base URL: {config.llm.ollama.base_url}")
            print(f"   Temperature: {config.llm.ollama.temperature}")
        
        # Create LLM instance
        print(f"\n🔧 Creating LLM instance...")
        manager = LLMManager()
        manager.reload()
        llm = manager.get_llm()
        
        print(f"✅ Success! LLM Type: {type(llm).__name__}")
        
        # Try to use the LLM for a simple test (may fail without valid API key)
        print(f"\n🧪 Testing LLM invocation...")
        try:
            from langchain_core.messages import HumanMessage
            response = llm.invoke([HumanMessage(content="Say 'Hello' in one word.")])
            print(f"✅ LLM Response: {response.content}")
        except Exception as e:
            print(f"⚠️  LLM invocation failed (this is expected without valid API keys/running server):")
            print(f"   Error: {type(e).__name__}: {str(e)[:100]}")
        
        # Test with orchestrator
        print(f"\n🤖 Testing with OrchestratorAgent...")
        from backend.agents.orchestrator import OrchestratorAgent
        orchestrator = OrchestratorAgent()
        print(f"✅ OrchestratorAgent created successfully with {type(orchestrator.llm).__name__}")
        
        print(f"\n✅ All tests passed for {provider_name}!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error testing {provider_name}:")
        print(f"   {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test function."""
    provider = sys.argv[1] if len(sys.argv) > 1 else 'ollama'
    
    if provider not in ['openai', 'gemini', 'ollama']:
        print(f"Invalid provider: {provider}")
        print("Valid options: openai, gemini, ollama")
        sys.exit(1)
    
    success = test_provider(provider)
    
    print(f"\n{'='*60}")
    print("Configuration Tips:")
    print('='*60)
    print("\n1. Environment Variables (highest priority):")
    print("   export LLM_PROVIDER=openai")
    print("   export OPENAI_API_KEY=your-key-here")
    print("   export OPENAI_MODEL=gpt-4")
    
    print("\n2. Configuration File (backend/config.yaml):")
    print("   llm:")
    print("     provider: openai")
    print("     openai:")
    print("       model: gpt-3.5-turbo")
    
    print("\n3. .env File (backend/.env):")
    print("   LLM_PROVIDER=openai")
    print("   OPENAI_API_KEY=your-key-here")
    
    print("\n" + "="*60 + "\n")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
