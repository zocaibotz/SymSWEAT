import sys
import os
import unittest

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils.parser import extract_json_content

class TestParser(unittest.TestCase):
    def test_clean_json(self):
        text = '{"key": "value"}'
        self.assertEqual(extract_json_content(text), {"key": "value"})

    def test_markdown_json(self):
        text = 'Here is the JSON:\n```json\n{"key": "value"}\n```'
        self.assertEqual(extract_json_content(text), {"key": "value"})

    def test_markdown_no_lang(self):
        text = '```\n{"key": "value"}\n```'
        self.assertEqual(extract_json_content(text), {"key": "value"})

    def test_chatter_around_json(self):
        text = 'Sure! Here is the output you requested:\n\n{"key": "value"}\n\nHope this helps!'
        self.assertEqual(extract_json_content(text), {"key": "value"})

    def test_nested_json(self):
        text = '{"outer": {"inner": "value"}}'
        self.assertEqual(extract_json_content(text), {"outer": {"inner": "value"}})

    def test_array_json(self):
        text = '[{"key": "value"}, {"key2": "value2"}]'
        self.assertEqual(extract_json_content(text), [{"key": "value"}, {"key2": "value2"}])

    def test_array_with_chatter(self):
        text = 'Here is the list:\n\n[{"key": "value"}]\n\nDone.'
        self.assertEqual(extract_json_content(text), [{"key": "value"}])

    def test_invalid_json(self):
        with self.assertRaises(ValueError):
            extract_json_content("This is just text with no JSON.")

if __name__ == "__main__":
    unittest.main()