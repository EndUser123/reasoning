#!/usr/bin/env python3
"""Simple prompt-based test for cognitive and reasoning telemetry.

This test verifies that both cognitive frameworks and reasoning modes
emit observable routing metadata without surfacing tag tokens to the LLM.

Usage:
    # Test cognitive frameworks
    echo "diagnose why the API is returning 500 errors" | python test_tag_emission.py cognitive

    # Test reasoning modes
    echo "should we use Redis or Memcached for caching?" | python test_tag_emission.py reasoning
"""

import sys


def test_cognitive_frameworks():
    """Test that cognitive frameworks emit telemetry without tag tokens."""
    from UserPromptSubmit_modules.base import HookContext
    from UserPromptSubmit_modules.cognitive_enhancers import cognitive_enhancers

    # Test diagnostic prompt (should trigger Cynefin + Hanlon's Razor)
    test_prompt = "diagnose why the API is returning 500 errors"

    context = HookContext(
        prompt=test_prompt,
        data={},
        session_id="test_session",
        terminal_id="test_terminal"
    )

    result = cognitive_enhancers(context)

    print("=== COGNITIVE FRAMEWORKS TEST ===")
    print(f"Prompt: {test_prompt}")
    print("\nInjected context:")
    print(result.context or "(no context)")
    print(f"\nTokens: {result.tokens}")

    # Verify telemetry is present without visible tag tokens
    if result.context and "Assumption Surfacing" in result.context and "[COG]" not in result.context:
        print("\n✓ Cognitive telemetry detected without tag token - PASS")
        return True
    else:
        print("\n✗ Cognitive telemetry missing or tag token leaked - FAIL")
        return False


def test_rationale_generation():
    """Test that telemetry includes a 'Why:' rationale line."""
    from UserPromptSubmit_modules.base import HookContext
    from UserPromptSubmit_modules.cognitive_enhancers import cognitive_enhancers

    print("=== RATIONALE GENERATION TEST ===")

    # Test case 1: Implementation prompt should show rationale
    test_prompt_1 = "implement a new authentication system"
    context_1 = HookContext(
        prompt=test_prompt_1,
        data={},
        session_id="test_session",
        terminal_id="test_terminal"
    )
    result_1 = cognitive_enhancers(context_1)

    print(f"Prompt: '{test_prompt_1}'")
    print(f"Context:\n{result_1.context or '(no context)'}")

    # Test case 2: Diagnostic prompt should show rationale
    test_prompt_2 = "diagnose why the API is returning 500 errors"
    context_2 = HookContext(
        prompt=test_prompt_2,
        data={},
        session_id="test_session",
        terminal_id="test_terminal"
    )
    result_2 = cognitive_enhancers(context_2)

    print(f"\nPrompt: '{test_prompt_2}'")
    print(f"Context:\n{result_2.context or '(no context)'}")

    # Verify behavior
    fail = False
    # Check Test 1
    if result_1.context and "Why:" in result_1.context:
        if "implementation intent detected" in result_1.context.lower():
            print("\n✓ Test 1: Implementation rationale present - PASS")
        else:
            print("\n✗ Test 1: Implementation rationale incorrect - FAIL")
            fail = True
    else:
        print("\n✗ Test 1: 'Why:' line missing - FAIL")
        fail = True

    # Check Test 2
    if result_2.context and "Why:" in result_2.context:
        if "diagnostic intent detected" in result_2.context.lower():
            print("✓ Test 2: Diagnostic rationale present - PASS")
        else:
            print("✗ Test 2: Diagnostic rationale incorrect - FAIL")
            fail = True
    else:
        print("✗ Test 2: 'Why:' line missing - FAIL")
        fail = True

    if not fail:
        print("\n✓ Rationale generation working correctly - PASS")

    return not fail


def test_config_validation():
    """Test that config validation emits warnings for missing 'enabled' key."""
    import sys
    import tempfile
    from pathlib import Path

    from UserPromptSubmit_modules.cognitive_enhancers import _load_config

    print("=== CONFIG VALIDATION TEST ===")

    # Test case 1: Valid config (no warnings expected)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{"enabled": true, "topics": {"implementation": true}}')
        valid_config_path = f.name

    try:
        # Temporarily override config path
        import UserPromptSubmit_modules.cognitive_enhancers as ce_module
        original_path = ce_module.CONFIG_PATH
        ce_module.CONFIG_PATH = Path(valid_config_path)

        # Reload config
        config = _load_config()

        print("Test 1: Valid config")
        print(f"Config loaded: enabled={config.get('enabled')}")

    finally:
        ce_module.CONFIG_PATH = original_path
        Path(valid_config_path).unlink()

    # Test case 2: Missing 'enabled' key (should emit warning)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{"topics": {"implementation": true}}')
        invalid_config_path = f.name

    try:
        # Capture stdout to check for warning
        import sys
        from io import StringIO
        old_stdout = sys.stdout
        sys.stdout = StringIO()

        ce_module.CONFIG_PATH = Path(invalid_config_path)
        config = _load_config()

        warning_output = sys.stdout.getvalue()
        sys.stdout = old_stdout

        print("\nTest 2: Missing 'enabled' key")
        print(f"Warning emitted: {bool(warning_output)}")
        if warning_output:
            print(f"Warning text: {warning_output.strip()[:100]}...")
        print(f"Config defaulted: enabled={config.get('enabled')}")

    finally:
        ce_module.CONFIG_PATH = original_path
        Path(invalid_config_path).unlink()

    # Test case 3: Invalid JSON (should emit error, already handled)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{"enabled": true, invalid json}')
        invalid_json_path = f.name

    try:
        old_stdout = sys.stdout
        sys.stdout = StringIO()

        ce_module.CONFIG_PATH = Path(invalid_json_path)
        config = _load_config()

        error_output = sys.stdout.getvalue()
        sys.stdout = old_stdout

        print("\nTest 3: Invalid JSON syntax")
        print(f"Error emitted: {bool(error_output)}")
        if error_output:
            print(f"Error text: {error_output.strip()[:100]}...")
        print(f"Config defaulted: enabled={config.get('enabled')}")

    finally:
        ce_module.CONFIG_PATH = original_path
        Path(invalid_json_path).unlink()

    # Verify behavior
    fail = False
    # Check Test 2 results
    if not warning_output:
        print("\n✗ Test 2 failed: No warning emitted for missing 'enabled' key - FAIL")
        fail = True

    # Check Test 3 results
    if not error_output:
        print("\n✗ Test 3 failed: No error emitted for invalid JSON - FAIL")
        fail = True

    if not fail:
        print("\n✓ Config validation working correctly - PASS")

    return not fail


def test_negation_handling():
    """Test that negation patterns don't trigger implementation intent."""
    from UserPromptSubmit_modules.cognitive_enhancers import _detect_intent

    print("=== NEGATION HANDLING TEST ===")

    # Test case 1: "don't implement X" should NOT trigger implementation
    test_prompt_1 = "don't implement a new authentication system"
    intent_1 = _detect_intent(test_prompt_1)

    print(f"Prompt: '{test_prompt_1}'")
    print(f"Implementation intent: {intent_1['implementation']}")

    # Test case 2: "don't create feature" should NOT trigger implementation
    test_prompt_2 = "don't create a new feature"
    intent_2 = _detect_intent(test_prompt_2)

    print(f"\nPrompt: '{test_prompt_2}'")
    print(f"Implementation intent: {intent_2['implementation']}")

    # Test case 3: "add tests to verify" SHOULD trigger implementation (no negation)
    test_prompt_3 = "add tests to verify the authentication"
    intent_3 = _detect_intent(test_prompt_3)

    print(f"\nPrompt: '{test_prompt_3}'")
    print(f"Implementation intent: {intent_3['implementation']}")

    # Test case 4: "make sure not to break" SHOULD trigger implementation (quality guidance)
    test_prompt_4 = "make sure not to break the existing code"
    intent_4 = _detect_intent(test_prompt_4)

    print(f"\nPrompt: '{test_prompt_4}'")
    print(f"Implementation intent: {intent_4['implementation']}")

    # Verify behavior
    fail = False
    if intent_1['implementation']:
        print("\n✗ 'don't implement' should NOT trigger implementation - FAIL")
        fail = True
    elif intent_2['implementation']:
        print("\n✗ 'don't create' should NOT trigger implementation - FAIL")
        fail = True
    elif not intent_3['implementation']:
        print("\n✗ 'add tests' SHOULD trigger implementation - FAIL")
        fail = True
    elif not intent_4['implementation']:
        print("\n✗ 'make sure not to break' SHOULD trigger implementation - FAIL")
        fail = True
    else:
        print("\n✓ Negation handling working correctly - PASS")

    return not fail


def test_confidence_threshold():
    """Test that low-confidence queries are skipped."""
    sys.path.insert(0, str(Path(__file__).resolve().parent / "hooks"))
    from Start_reasoning_mode_selector import analyze_query, process_prompt

    print("=== CONFIDENCE THRESHOLD TEST ===")

    # Test case 1: Confidence 0 (should skip)
    test_query_0 = "hello"
    result_0 = analyze_query(test_query_0)
    data_0 = {"query": test_query_0}
    output_0 = process_prompt(data_0)

    print(f"Query: '{test_query_0}' (confidence: {result_0['confidence']}/4)")
    print(f"Output: {output_0.get('additionalContext', '(empty dict)')}")

    # Test case 2: Confidence 1 (should skip)
    test_query_1 = "what is"
    result_1 = analyze_query(test_query_1)
    data_1 = {"query": test_query_1}
    output_1 = process_prompt(data_1)

    print(f"\nQuery: '{test_query_1}' (confidence: {result_1['confidence']}/4)")
    print(f"Output: {output_1.get('additionalContext', '(empty dict)')}")

    # Test case 3: Confidence 2+ (should inject)
    test_query_2 = "explain how to implement OAuth 2.0"
    result_2 = analyze_query(test_query_2)
    data_2 = {"query": test_query_2}
    output_2 = process_prompt(data_2)

    print(f"\nQuery: '{test_query_2}' (confidence: {result_2['confidence']}/4)")
    print(f"Output: {output_2.get('additionalContext', '(empty dict)')}")

    # Verify threshold behavior
    fail = False
    if result_0['confidence'] < 2 and output_0.get('additionalContext'):
        print("\n✗ Confidence 0 should skip injection - FAIL")
        fail = True
    elif result_1['confidence'] < 2 and output_1.get('additionalContext'):
        print("\n✗ Confidence 1 should skip injection - FAIL")
        fail = True
    elif result_2['confidence'] >= 2 and not output_2.get('additionalContext'):
        print("\n✗ Confidence 2+ should inject - FAIL")
        fail = True
    else:
        print("\n✓ Confidence threshold working correctly - PASS")

    return not fail


def test_reasoning_modes():
    """Test that reasoning mode selector injects mode context."""
    # Import the reasoning mode selector
    sys.path.insert(0, str(Path(__file__).resolve().parent / "hooks"))
    from Start_reasoning_mode_selector import process_prompt

    # Test comparison prompt (should trigger multi_agent)
    test_query = "should we use Redis or Memcached for caching?"

    data = {"query": test_query}
    result = process_prompt(data)

    print("=== REASONING MODES TEST ===")
    print(f"Query: {test_query}")
    print("\nInjected context:")
    print(result.get("additionalContext", "(no context)"))
    print(f"\nTokens: {result.get('tokens', 0)}")

    # Verify reasoning mode is mentioned
    context = result.get("additionalContext", "")
    if "multi_agent" in context.lower():
        print("\n✓ Reasoning mode detected - PASS")
        return True
    else:
        print("\n✗ Reasoning mode NOT detected - FAIL")
        return False


if __name__ == "__main__":
    from pathlib import Path

    if len(sys.argv) < 2:
        print("Usage: python test_tag_emission.py [cognitive|reasoning|confidence|negation|config|rationale]")
        sys.exit(1)

    test_type = sys.argv[1].lower()

    if test_type == "cognitive":
        success = test_cognitive_frameworks()
    elif test_type == "reasoning":
        success = test_reasoning_modes()
    elif test_type == "confidence":
        success = test_confidence_threshold()
    elif test_type == "negation":
        success = test_negation_handling()
    elif test_type == "config":
        success = test_config_validation()
    elif test_type == "rationale":
        success = test_rationale_generation()
    else:
        print(f"Unknown test type: {test_type}")
        print("Use 'cognitive', 'reasoning', 'confidence', 'negation', 'config', or 'rationale'")
        sys.exit(1)

    sys.exit(0 if success else 1)
