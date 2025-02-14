import unittest
from xutils.app_config import Domain, AppConfig, RunConfig, CombinedConfig
from xutils.embedding_config import EmbeddingConfig


class TestAppConfig(unittest.TestCase):

    def setUp(self):
        self.embed_config = EmbeddingConfig(
            prefix="test-prefix",
            max_len=100,
        )

    def test_domain_enum(self):
        """Test Domain enum values"""
        self.assertEqual(Domain.WIKI.value, "wiki")
        self.assertEqual(Domain.PLOTS.value, "plots")
        self.assertEqual(len(Domain), 2)

    def test_app_config(self):
        """Test AppConfig dataclass"""
        embed_config = self.embed_config
        config = AppConfig(
            domain=Domain.WIKI,
            text_file_path="/path/to/file",
            embed_config=embed_config
        )

        self.assertEqual(config.domain, Domain.WIKI)
        self.assertEqual(config.text_file_path, "/path/to/file")
        self.assertEqual(config.embed_config, embed_config)

        # Test with optional embed_config as None
        config_no_embed = AppConfig(
            domain=Domain.PLOTS,
            text_file_path="/path/to/file",
            embed_config=None
        )
        self.assertIsNone(config_no_embed.embed_config)

    def test_run_config(self):
        """Test RunConfig dataclass"""
        config = RunConfig(
            hostname="localhost",
            port=8080,
            log_level="INFO"
        )

        self.assertEqual(config.hostname, "localhost")
        self.assertEqual(config.port, 8080)
        self.assertEqual(config.log_level, "INFO")

    def test_combined_config(self):
        """Test CombinedConfig dataclass"""
        run_config = RunConfig(
            hostname="localhost",
            port=8080,
            log_level="INFO"
        )

        embed_config = self.embed_config

        config = CombinedConfig(
            domain=Domain.WIKI,
            text_file_path="/path/to/file",
            embed_config=embed_config,
            k=5,
            threshold=0.8,
            max_documents=100,
            run_config=run_config
        )

        # Test inherited fields from AppConfig
        self.assertEqual(config.domain, Domain.WIKI)
        self.assertEqual(config.text_file_path, "/path/to/file")
        self.assertEqual(config.embed_config, embed_config)

        # Test CombinedConfig specific fields
        self.assertEqual(config.k, 5)
        self.assertEqual(config.threshold, 0.8)
        self.assertEqual(config.max_documents, 100)
        self.assertEqual(config.run_config, run_config)


if __name__ == "__main__":
    unittest.main()
