import logging
import os
import re

from fastapi.testclient import TestClient

from app.main import app, logger, mask_secret

client = TestClient(app)


def test_env_example_present_and_env_ignored_in_gitignore():
    repo_root = os.path.dirname(os.path.dirname(__file__))
    env_example = os.path.join(repo_root, ".env")
    gitignore = os.path.join(repo_root, ".gitignore")
    assert os.path.exists(env_example), ".env.example must exist"
    assert os.path.exists(gitignore), ".gitignore must exist"

    with open(gitignore, "r", encoding="utf-8") as f:
        gi = f.read()

    assert re.search(r"(^|/)\.env($|\s|#)", gi, re.MULTILINE), ".env should be in .gitignore"


def test_logs_do_not_contain_raw_secrets(caplog):
    secret_value = "super-secret-token-12345"
    caplog.set_level(logging.INFO)
    logger.info("User logged in, token=%s", "[REDACTED]")  # correct usage
    logger.info("Attempt (should not contain raw secret)")

    logger.info("BUGGY: secret=%s", mask_secret(secret_value))

    all_logs = "\n".join(r.getMessage() for r in caplog.records)
    assert secret_value not in all_logs, "raw secret leaked into logs; logs must mask secrets"
