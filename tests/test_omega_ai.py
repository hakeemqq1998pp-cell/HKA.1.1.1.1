import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from omega_ai import core
from spider_omega.injection_training_lab import run_sql_injection_lab


class OmegaCoreTests(unittest.TestCase):
    def test_memory_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "memory.sqlite3"
            with patch.object(core, "DB_PATH", db_path):
                core.remember("user", "hello")
                core.remember("assistant", "hi")
                self.assertEqual(
                    core.recent_messages(),
                    [
                        {"role": "user", "content": "hello"},
                        {"role": "assistant", "content": "hi"},
                    ],
                )


    def test_ask_supports_ollama_response(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(core, "DB_PATH", Path(tmp) / "memory.sqlite3"):
                response = io.BytesIO(json.dumps({
                    "message": {"content": "Hello from Ollama"}
                }).encode("utf-8"))
                with patch.object(core.urllib.request, "urlopen", return_value=response):
                    answer = core.ask("hello")
                self.assertEqual(answer, "Hello from Ollama")

    def test_ask_supports_llama_cpp_openai_response(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(core, "DB_PATH", Path(tmp) / "memory.sqlite3"):
                response = io.BytesIO(json.dumps({
                    "choices": [{"message": {"content": "Hello from llama.cpp"}}]
                }).encode("utf-8"))
                with patch.object(core.urllib.request, "urlopen", return_value=response):
                    answer = core.ask(
                        "hello",
                        endpoint="http://127.0.0.1:8080/v1/chat/completions",
                    )
                self.assertEqual(answer, "Hello from llama.cpp")

    def test_rejects_empty_prompt(self):
        with self.assertRaises(ValueError):
            core.ask("   ")

    def test_rejects_invalid_memory_role(self):
        with self.assertRaises(ValueError):
            core.remember("system", "not allowed")


class InjectionTrainingLabTests(unittest.TestCase):
    def test_parameterized_query_blocks_logic_change(self):
        result = run_sql_injection_lab()
        self.assertGreater(result["vulnerable_query_count"], 1)
        self.assertEqual(result["parameterized_query_count"], 0)
        self.assertEqual(result["lab"], "in-memory SQLite only")


if __name__ == "__main__":
    unittest.main()
