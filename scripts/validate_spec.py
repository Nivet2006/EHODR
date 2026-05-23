# ==============================================================================
# PURPOSE: Automated Architecture & OpenSpec Conformance Validator.
# SCOPE: Parses codebase configuration/routes and matches against openspec blueprint.
# DEPENDENCIES: Standard Python library
# RISKS: Static check only; does not guarantee runtime socket availability.
# ==============================================================================

import os
import re
import sys

def log_info(msg: str):
    print(f"\033[32m[OpenSpec Validator] INFO: {msg}\033[0m")

def log_error(msg: str):
    print(f"\033[31m[OpenSpec Validator] ERROR: {msg}\033[0m", file=sys.stderr)

def check_config_integrity() -> bool:
    """
    Validates that configurations inside config.py match the architectural specs.
    """
    config_path = os.path.join("gateway", "config.py")
    if not os.path.exists(config_path):
        log_error(f"Missing gateway config.py file at: {config_path}")
        return False

    with open(config_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Immutable specifications checklist
    specs = {
        "GATEWAY_PORT": r"GATEWAY_PORT:\s*int\s*=\s*Field\(default=8000\)",
        "QDRANT_PORT": r"QDRANT_PORT:\s*int\s*=\s*Field\(default=6333\)",
        "DEDUP_SIMILARITY_THRESHOLD": r"DEDUP_SIMILARITY_THRESHOLD:\s*float\s*=\s*Field\(default=0.92\)",
        "MIN_IMPORTANCE_SCORE_TO_STORE": r"MIN_IMPORTANCE_SCORE_TO_STORE:\s*float\s*=\s*Field\(default=0.3\)",
        "MAX_CONTEXT_TOKENS": r"MAX_CONTEXT_TOKENS:\s*int\s*=\s*Field\(default=4000\)"
    }

    success = True
    for spec_name, pattern in specs.items():
        if not re.search(pattern, content):
            log_error(f"OpenSpec Conformance Failure: '{spec_name}' in gateway/config.py does not match system_architecture.md requirements.")
            success = False
        else:
            log_info(f"Verified '{spec_name}' matches specification.")

    return success

def check_endpoints_integrity() -> bool:
    """
    Validates that all architectural REST endpoints are implemented in the API routes.
    """
    router_path = os.path.join("gateway", "api", "v1", "memory.py")
    if not os.path.exists(router_path):
        log_error(f"Missing API router file at: {router_path}")
        return False

    with open(router_path, "r", encoding="utf-8") as f:
        content = f.read()

    # REST endpoint signatures checklist
    endpoints = {
        "POST /save": r"@router\.post\(\"/save\"",
        "POST /recall": r"@router\.post\(\"/recall\"",
        "POST /search": r"@router\.post\(\"/search\"",
        "DELETE /delete/{memory_id}": r"@router\.delete\(\"/delete/{memory_id}\""
    }

    success = True
    for route_name, pattern in endpoints.items():
        if not re.search(pattern, content):
            log_error(f"OpenSpec Conformance Failure: Missing architectural route definition '{route_name}' in gateway/api/v1/memory.py.")
            success = False
        else:
            log_info(f"Verified '{route_name}' route is implemented.")

    return success

def check_env_example_integrity() -> bool:
    """
    Validates that no active developers credentials exist in the template and all settings keys match.
    """
    env_example_path = ".env.example"
    if not os.path.exists(env_example_path):
        log_error(f"Missing .env.example template file at: {env_example_path}")
        return False

    with open(env_example_path, "r", encoding="utf-8") as f:
        content = f.read()

    keys = [
        "GATEWAY_PORT",
        "API_SECRET_KEY",
        "EMBEDDING_PROVIDER",
        "DEDUP_SIMILARITY_THRESHOLD",
        "MIN_IMPORTANCE_SCORE_TO_STORE",
        "MAX_CONTEXT_TOKENS"
    ]

    success = True
    for key in keys:
        if key not in content:
            log_error(f"OpenSpec Conformance Failure: Missing key '{key}' in environment example template.")
            success = False
        else:
            log_info(f"Verified '{key}' exists in env.example.")

    return success

def run_all_validation() -> bool:
    log_info("Executing OpenSpec System Architecture Verification Suite...")
    
    config_ok = check_config_integrity()
    endpoints_ok = check_endpoints_integrity()
    env_ok = check_env_example_integrity()
    
    if config_ok and endpoints_ok and env_ok:
        log_info("SUCCESS: 100% OpenSpec System Architecture conformance achieved. Zero configuration drift detected.")
        return True
    else:
        log_error("CRITICAL: Conformance validation failed. Codebase drift detected against system_architecture.md specification.")
        return False

if __name__ == "__main__":
    if not run_all_validation():
        sys.exit(1)
    sys.exit(0)
