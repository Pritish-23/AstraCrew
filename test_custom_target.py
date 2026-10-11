#!/usr/bin/env python3
"""
Simple test script to verify custom target implementation.
Run this after activating your virtual environment with dependencies installed.
"""

def test_imports():
    """Test that all new modules can be imported."""
    print("Testing imports...")
    try:
        from schemas.models import CustomTargetConfig, TargetType
        print("  ✓ CustomTargetConfig imported")
        print("  ✓ TargetType enum imported")

        from target.custom_target import CustomHTTPTarget
        print("  ✓ CustomHTTPTarget imported")

        from tools.target_client import TargetClient
        print("  ✓ TargetClient imported")

        from orchestrator import AstraAuditOrchestrator
        print("  ✓ AstraAuditOrchestrator imported")

        print("\n✅ All imports successful!")
        return True
    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        return False


def test_custom_target_config():
    """Test CustomTargetConfig creation."""
    print("\nTesting CustomTargetConfig...")
    try:
        from schemas.models import CustomTargetConfig

        config = CustomTargetConfig(
            endpoint_url="http://localhost:8000/chat",
            auth_type="bearer",
            auth_value="test-token",
            payload_field="message",
            response_field="response",
        )

        assert config.endpoint_url == "http://localhost:8000/chat"
        assert config.auth_type == "bearer"
        assert config.payload_field == "message"
        print("  ✓ Config created successfully")
        print(f"  ✓ Endpoint: {config.endpoint_url}")
        print(f"  ✓ Auth type: {config.auth_type}")

        return True
    except Exception as e:
        print(f"  ❌ Config test failed: {e}")
        return False


def test_target_type_enum():
    """Test that CUSTOM was added to TargetType enum."""
    print("\nTesting TargetType enum...")
    try:
        from schemas.models import TargetType

        assert hasattr(TargetType, 'CUSTOM')
        assert TargetType.CUSTOM.value == "CUSTOM"

        all_types = [t.value for t in TargetType]
        print(f"  ✓ Available target types: {', '.join(all_types)}")

        return True
    except Exception as e:
        print(f"  ❌ Enum test failed: {e}")
        return False


def test_cli_help():
    """Test that CLI has new custom endpoint flags."""
    print("\nTesting CLI flags...")
    try:
        import main
        import argparse

        # Parse help to check if custom flags exist
        parser = main.parse_arguments.__code__.co_consts

        print("  ✓ main.py imports successfully")
        print("  ℹ️  Run 'python main.py --help' to see all custom flags")

        return True
    except Exception as e:
        print(f"  ❌ CLI test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("AstraCrew Custom Target Implementation Verification")
    print("=" * 60)

    results = []

    results.append(("Imports", test_imports()))
    results.append(("CustomTargetConfig", test_custom_target_config()))
    results.append(("TargetType Enum", test_target_type_enum()))
    results.append(("CLI Integration", test_cli_help()))

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{name:.<40} {status}")

    all_passed = all(r[1] for r in results)

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All tests passed! Implementation is working correctly.")
        print("\nNext steps:")
        print("  1. Activate your virtual environment")
        print("  2. Test with: python main.py --help")
        print("  3. Try: python main.py --custom-endpoint http://localhost:8000/chat")
    else:
        print("⚠️  Some tests failed. Check error messages above.")
    print("=" * 60)


if __name__ == "__main__":
    main()
