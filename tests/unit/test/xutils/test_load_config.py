import os
import sys
import io
import tempfile
import unittest
import logging
import configparser
from unittest.mock import patch
from contextlib import contextmanager

# Import functions and classes to test
from xutils.load_config import (
    load_app_config,
    load_embed_config,
    load_run_config,
    parse_args,
    get_app_config_and_query,
    get_app_config,
)
from search.services.combined_service import Action
from xutils.app_config import Domain, RunConfig
from xutils.embedding_config import EmbeddingConfig


@contextmanager
def suppress_stderr():
    """Temporarily suppress stderr output"""
    stderr = sys.stderr
    sys.stderr = io.StringIO()
    try:
        yield
    finally:
        sys.stderr = stderr


# A sample config file content for testing
CONFIG_TEXT = """
[SEARCH-APP]
domain = wiki
text-file-path = /path/to/text
k = 10
threshold = 0.5
max-documents = 50

[SEARCH-APP.EMBEDDINGS]
prefix = emb_
max-len = 200
dim = 128
stype = float64
norm-type = l2
l2-normalize = yes

[SEARCH-APP.RUN]
hostname = localhost
port = 9090
log-level = DEBUG
"""


class TestLoadConfig(unittest.TestCase):
    def setUp(self):
        # Create a dummy logger for testing
        self.logger = logging.getLogger("TestLoadConfig")
        self.logger.setLevel(logging.DEBUG)

    def create_temp_config_file(self, content=CONFIG_TEXT):
        """Helper function to create a temporary config file."""
        tmp_file = tempfile.NamedTemporaryFile(delete=False, mode="w")
        tmp_file.write(content)
        tmp_file.close()
        return tmp_file.name

    def test_load_app_config(self):
        """
        Test that load_app_config correctly parses the config file.
        """
        tmp_config_path = self.create_temp_config_file()
        # Patch the environment variable CONFIG_FILE to point to our temp file
        with patch.dict(os.environ, {"CONFIG_FILE": tmp_config_path}):
            config = load_app_config(self.logger)
            # Assert CombinedConfig fields from SEARCH-APP section
            self.assertEqual(config.domain, Domain.WIKI)
            self.assertEqual(config.text_file_path, "/path/to/text")
            self.assertEqual(config.k, 10)
            self.assertAlmostEqual(config.threshold, 0.5)
            self.assertEqual(config.max_documents, 50)

            # Assert embed_config values
            embed = config.embed_config
            self.assertIsInstance(embed, EmbeddingConfig)
            self.assertEqual(embed.prefix, "emb_")
            self.assertEqual(embed.max_len, 200)
            self.assertEqual(embed.dim, 128)
            self.assertEqual(embed.stype, "float64")
            self.assertEqual(embed.norm_type, "l2")
            self.assertTrue(embed.l2_normalize)

            # Assert run_config values
            run = config.run_config
            self.assertIsInstance(run, RunConfig)
            self.assertEqual(run.hostname, "localhost")
            self.assertEqual(run.port, 9090)
            self.assertEqual(run.log_level, "DEBUG")

        # Clean up our temporary file
        os.remove(tmp_config_path)

    def test_load_embed_config_and_run_config(self):
        """
        Test load_embed_config and load_run_config functions with a ConfigParser.
        """
        config_parser = configparser.ConfigParser()
        config_parser.read_string(CONFIG_TEXT)

        embed_config = load_embed_config(config_parser)
        self.assertEqual(embed_config.prefix, "emb_")
        self.assertEqual(embed_config.max_len, 200)
        self.assertEqual(embed_config.dim, 128)
        self.assertEqual(embed_config.stype, "float64")
        self.assertEqual(embed_config.norm_type, "l2")
        self.assertTrue(embed_config.l2_normalize)

        run_config = load_run_config(config_parser)
        self.assertEqual(run_config.hostname, "localhost")
        self.assertEqual(run_config.port, 9090)
        self.assertEqual(run_config.log_level, "DEBUG")

    def test_parse_args_with_search_marker(self):
        """
        Test that parse_args correctly processes query ending with :search.
        """
        test_args = ["prog", "hello", "world:search"]
        with patch.object(sys, "argv", test_args):
            args = parse_args(expect_query=True)
            self.assertEqual(args.query, "hello world")
            self.assertEqual(args.action, Action.SEARCH)

    def test_parse_args_with_rag_marker(self):
        """
        Test that parse_args correctly processes query ending with :rag.
        """
        test_args = ["prog", "this", "is", "a", "test:rag"]
        with patch.object(sys, "argv", test_args):
            args = parse_args(expect_query=True)
            self.assertEqual(args.query, "this is a test")
            self.assertEqual(args.action, Action.RAG)

    def test_parse_args_no_query_error(self):
        """
        Test that parse_args raises an error when expect_query is True but no query is provided.
        """
        test_args = ["prog"]
        with suppress_stderr():
            with patch.object(sys, "argv", test_args):
                with self.assertRaises(SystemExit):
                    parse_args(expect_query=True)

    def test_parse_args_no_query_not_required(self):
        """
        Test that parse_args works when expect_query is False even if no query is provided.
        """
        test_args = ["prog"]
        with patch.object(sys, "argv", test_args):
            args = parse_args(expect_query=False)
            # With no query parts the joined query is an empty string.
            self.assertEqual(args.query, "")
            self.assertEqual(args.action, Action.SEARCH)

    def test_parse_args_with_custom_action(self):
        """
        Test that parse_args retains a custom --action value if no marker is provided.
        """
        test_args = ["prog", "--action", "custom", "foo", "bar"]
        with patch.object(sys, "argv", test_args):
            args = parse_args(expect_query=True)
            self.assertEqual(args.query, "foo bar")
            self.assertEqual(args.action, "custom")

    def test_get_app_config_and_query(self):
        """
        Test that get_app_config_and_query returns the correct app_config, query, and action.
        """
        tmp_config_path = self.create_temp_config_file()
        with patch.dict(os.environ, {"CONFIG_FILE": tmp_config_path}):
            test_args = ["prog", "test", "query:rag"]
            with patch.object(sys, "argv", test_args):
                app_config, query, action = get_app_config_and_query(self.logger)
                # Verify parsed query and action
                self.assertEqual(query, "test query")
                self.assertEqual(action, Action.RAG)
                # Verify that the returned app_config matches the config file
                self.assertEqual(app_config.text_file_path, "/path/to/text")
                self.assertEqual(app_config.k, 10)
        os.remove(tmp_config_path)

    def test_get_app_config_with_overrides(self):
        """
        Test that get_app_config applies command line overrides.
        """
        tmp_config_path = self.create_temp_config_file()
        with patch.dict(os.environ, {"CONFIG_FILE": tmp_config_path}):
            # Provide overrides for hostname and port via command line. No query expected.
            test_args = ["prog", "--hostname", "override_host", "--port", "1234"]
            with patch.object(sys, "argv", test_args):
                app_config = get_app_config(self.logger)
                self.assertEqual(app_config.run_config.hostname, "override_host")
                # Port should be overridden to 1234
                self.assertEqual(app_config.run_config.port, 1234)
        os.remove(tmp_config_path)


if __name__ == "__main__":
    unittest.main()
