import unittest
from spider_omega.scanner import analyze_url
from spider_omega.phishing_lab import analyze_email

class ScannerTests(unittest.TestCase):
    def test_http_flag(self):
        self.assertIn("Unencrypted HTTP connection",
                      analyze_url("http://example.com")["flags"])
    def test_userinfo_flag(self):
        self.assertTrue(any("User information" in x for x in
                            analyze_url("https://user:pass@example.com")["flags"]))
    def test_https_domain(self):
        self.assertEqual(analyze_url("https://example.com")["host"], "example.com")
    def test_email_urgency(self):
        self.assertEqual(analyze_email("URGENT: verify your account immediately")["risk"], "MEDIUM")

if __name__ == "__main__":
    unittest.main()
