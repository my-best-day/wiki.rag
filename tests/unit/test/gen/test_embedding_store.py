import unittest
import importlib
import numpy as np
import numpy.testing as npt
from uuid import uuid4
from pathlib import Path
from unittest.mock import MagicMock, patch
from gen.embedding_store import CleanFileLock, EMPTY_RESULT
from gen.embedding_store import StoreMode
from gen.uuid_embedding_store import UUIDEmbeddingStore
from xutils.embedding_config import EmbeddingConfig


class CleanFileLockTestCase(unittest.TestCase):
    def test_exit(self):
        # test: lock file is removed after release
        path = "/fake/path"
        lock = CleanFileLock(path)
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True
            with patch("os.unlink") as mock_unlink:
                lock.__exit__(None, None, None)
                mock_exists.assert_called_once_with(path)
                mock_unlink.assert_called_once_with(path)

        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = False
            with patch("os.unlink") as mock_unlink:
                lock.__exit__(None, None, None)
                mock_exists.assert_called_once_with(path)
                mock_unlink.assert_not_called()


class TestCleanFileLock:

    instances = []

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.enter_call_count = 0
        self.exit_call_count = 0
        TestCleanFileLock.instances.append(self)

    def __enter__(self):
        self.enter_call_count += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.exit_call_count += 1


class TestEmbeddingStore(unittest.TestCase):

    def setUp(self):
        TestCleanFileLock.instances.clear()
        UUIDEmbeddingStore.file_lock_class = TestCleanFileLock

    def tearDown(self):
        module = importlib.import_module(UUIDEmbeddingStore.__module__)
        importlib.reload(module)

    def test_lock_path(self):
        path = "/fake/path"
        store = UUIDEmbeddingStore(path, mode=StoreMode.INCREMENTAL, allow_empty=True)
        self.assertEqual(str(store.lock_path), f"{path}.lock")
        self.assertIsInstance(store.lock_path, Path)

    def test_extend_embeddings(self):
        # test: lock is used, _add_embeddings was called, uids were cast to strings
        path = "/fake/path"
        store = UUIDEmbeddingStore(path, mode=StoreMode.INCREMENTAL, allow_empty=True)
        store._add_embeddings = MagicMock()

        uids = [uuid4(), uuid4()]
        stringified_uids = [str(uid) for uid in uids]
        embeddings = np.array([[1, 2, 3], [4, 5, 6]])
        store.extend_embeddings(uids, embeddings)

        self.assertEqual(len(TestCleanFileLock.instances), 1)
        file_lock = TestCleanFileLock.instances[0]
        self.assertIsInstance(file_lock, TestCleanFileLock)
        self.assertEqual(file_lock.enter_call_count, 1)
        self.assertEqual(file_lock.exit_call_count, 1)
        store._add_embeddings.assert_called_once_with(stringified_uids, embeddings)

    def test_extend_embeddings_empty(self):
        # test: lock is used, _add_embeddings was called, uids were cast to strings
        path = "/fake/path"
        store = UUIDEmbeddingStore(path, mode=StoreMode.INCREMENTAL, allow_empty=True)
        store._add_embeddings = MagicMock()

        uids = []
        stringified_uids = [str(uid) for uid in uids]
        embeddings = []
        store.extend_embeddings(uids, embeddings)

        self.assertEqual(len(TestCleanFileLock.instances), 1)
        file_lock = TestCleanFileLock.instances[0]
        self.assertIsInstance(file_lock, TestCleanFileLock)
        self.assertEqual(file_lock.enter_call_count, 1)
        self.assertEqual(file_lock.exit_call_count, 1)
        store._add_embeddings.assert_called_once_with(stringified_uids, embeddings)

    def test_protected_add_embeddings_init(self):
        # test: incremental addition... from scratch
        path = "/dev/null"
        store = UUIDEmbeddingStore(path, mode=StoreMode.INCREMENTAL, allow_empty=True)
        empty_uids, empty_embeddings = EMPTY_RESULT
        store._load_embeddings = MagicMock(return_value=(empty_uids, empty_embeddings))

        np.savez = MagicMock()

        uids = [uuid4(), uuid4()]
        stringified_uids = [str(uid) for uid in uids]
        embeddings = np.array([[1, 2, 3], [4, 5, 6]])
        store._add_embeddings(stringified_uids, embeddings)

        store._load_embeddings.assert_called_once()
        np.savez.assert_called_once_with(Path(path), uids=stringified_uids, embeddings=embeddings)

    def test_protected_add_embeddings_init_empty(self):
        # test: incremental addition... from scratch
        path = "/dev/null"
        store = UUIDEmbeddingStore(path, mode=StoreMode.INCREMENTAL, allow_empty=True)
        empty_uids, empty_embeddings = EMPTY_RESULT
        store._load_embeddings = MagicMock(return_value=(empty_uids, empty_embeddings))

        np.savez = MagicMock()

        uids = []
        stringified_uids = [str(uid) for uid in uids]
        embeddings = np.array([])
        store._add_embeddings(stringified_uids, embeddings)

        store._load_embeddings.assert_not_called()
        np.savez.assert_not_called()

    def test_protected_add_embeddings_append(self):
        # test: incremental addition with existing entries
        path = "/dev/null"
        store = UUIDEmbeddingStore(path, mode=StoreMode.INCREMENTAL, allow_empty=True)
        existing_uids = np.array([str(uuid4()), str(uuid4())])
        existing_embeddings = np.array([[7, 8, 9], [10, 11, 12]])
        store._load_embeddings = MagicMock(return_value=(
            existing_uids, existing_embeddings))

        np.savez = MagicMock()

        uids = [str(uuid4()), str(uuid4())]
        embeddings = np.array([[1, 2, 3], [4, 5, 6]])
        expected_uids = np.concatenate((existing_uids, uids))
        expected_embeddings = np.concatenate((existing_embeddings, embeddings))
        store._add_embeddings(uids, embeddings)

        np.savez.assert_called_once()
        _, kwargs = np.savez.call_args  # Get the call arguments
        npt.assert_array_equal(kwargs["uids"], expected_uids)
        npt.assert_array_equal(kwargs["embeddings"], expected_embeddings)

    def test_protected_add_embeddings_append_empty(self):
        # test: incremental addition with existing entries
        path = "/dev/null"
        store = UUIDEmbeddingStore(path, mode=StoreMode.INCREMENTAL, allow_empty=True)
        existing_uids = np.array([str(uuid4()), str(uuid4())])
        existing_embeddings = np.array([[7, 8, 9], [10, 11, 12]])
        store._load_embeddings = MagicMock(return_value=(
            existing_uids, existing_embeddings))

        np.savez = MagicMock()

        uids = []
        embeddings = np.array([])
        store._add_embeddings(uids, embeddings)

        np.savez.assert_not_called()

    def test_protected_add_embeddings_do_not_stringify(self):
        # stringifying uids is the public method responsibility, don't do it here
        path = "/dev/null"
        store = UUIDEmbeddingStore(path, mode=StoreMode.INCREMENTAL, allow_empty=True)
        empty_uids, empty_embeddings = EMPTY_RESULT
        store._load_embeddings = MagicMock(return_value=(empty_uids, empty_embeddings))

        np.savez = MagicMock()

        uids = [uuid4(), uuid4()]
        embeddings = np.array([[1, 2, 3], [4, 5, 6]])
        store._add_embeddings(uids, embeddings)

        store._load_embeddings.assert_called_once()
        np.savez.assert_called_once_with(Path(path), uids=uids, embeddings=embeddings)

    def test_get_count(self):
        # test count for zero and none zero entries
        path = "/fake/path"
        store = UUIDEmbeddingStore(path, mode=StoreMode.INCREMENTAL, allow_empty=True)

        store._load_embeddings = MagicMock(return_value=(np.array([]), np.array([])))
        self.assertEqual(store.get_count(), 0)

        store._load_embeddings = MagicMock(return_value=(np.array(['s1', 's2']), np.array([])))
        self.assertEqual(store.get_count(), 2)

    def test_load_embeddings(self):
        # test: lock is used, _load_embeddings was called, uids were cast to UUIDS
        path = "/fake/path"
        store = UUIDEmbeddingStore(path, mode=StoreMode.READ, allow_empty=True)

        uids = np.array([uuid4(), uuid4()])
        stringified_uids = uids.astype(str)
        embeddings = np.array([[1, 2, 3], [4, 5, 6]])

        store._load_embeddings = MagicMock()
        store._load_embeddings.return_value = (stringified_uids, embeddings)

        out_uids, out_embeddings = store.load_uuid_embeddings()

        self.assertEqual(len(TestCleanFileLock.instances), 1)
        file_lock = TestCleanFileLock.instances[0]
        self.assertIsInstance(file_lock, TestCleanFileLock)
        self.assertEqual(file_lock.enter_call_count, 1)
        self.assertEqual(file_lock.exit_call_count, 1)
        npt.assert_array_equal(out_uids, uids)
        npt.assert_array_equal(out_embeddings, embeddings)

    @patch.object(UUIDEmbeddingStore, "does_store_exist", return_value=False)
    def test_protected_load_embeddings_no_file_ctor(self, does_store_exist_mock):
        path = "/dev/null/store.json"
        with self.assertRaises(RuntimeError):
            UUIDEmbeddingStore(path, mode=StoreMode.READ, allow_empty=False)

    def test_protected_load_embeddings_stores_does_not_exist(self):
        # test: no store
        path = "/dev/null"
        store = UUIDEmbeddingStore(path, mode=StoreMode.READ, allow_empty=True)
        store.does_store_exist = MagicMock(return_value=False)

        uids, embeddings = store._load_embeddings(allow_empty=True)
        self.assertEqual(uids.size, 0)
        self.assertEqual(embeddings.size, 0)

        with self.assertRaises(FileNotFoundError):
            store._load_embeddings(allow_empty=False)

    def test_protected_load_embeddings_store_exists(self):
        # test: empty store
        path = "/dev/null"
        store = UUIDEmbeddingStore(path, mode=StoreMode.READ, allow_empty=True)
        store.does_store_exist = MagicMock(return_value=True)

        uids = [uuid4(), uuid4()]
        stringified_uids = np.array([str(uid) for uid in uids])
        embeddings = np.array([[1, 2, 3], [4, 5, 6]])
        mocked_data = {"uids": stringified_uids, "embeddings": embeddings}

        mock_np_load = MagicMock()
        mock_np_load.return_value.__enter__.return_value = mocked_data

        with patch("numpy.load", mock_np_load):
            out_uids, out_embeddings = store._load_embeddings(allow_empty=False)
            mock_np_load.assert_called_once_with(Path(path))
            npt.assert_array_equal(out_uids, stringified_uids)
            npt.assert_array_equal(out_embeddings, embeddings)

    def test_does_store_exists(self):
        # test: file exists
        path = "/fake/path"
        store = UUIDEmbeddingStore(path, mode=StoreMode.READ, allow_empty=True)
        with patch.object(Path, "exists", return_value=False):
            self.assertFalse(store.does_store_exist())

    def test_get_store_path(self):
        config = EmbeddingConfig(
            prefix="/fake/path",
            max_len=10,
            dim=768,
            stype="float16",
            norm_type="int8",
            l2_normalize=True
        )

        store = UUIDEmbeddingStore
        path = store.get_store_path(config)
        expected_path = "/fake/path_10_768_float16_embeddings.npz"
        self.assertEqual(path, expected_path)

        config.dim = None
        path = store.get_store_path(config)
        expected_path = "/fake/path_10_float16_embeddings.npz"
        self.assertEqual(path, expected_path)

        config.dim = 256
        config.max_len = 20
        config.stype = "float32"
        path = store.get_store_path(config)
        expected_path = "/fake/path_20_256_embeddings.npz"
        self.assertEqual(path, expected_path)

        config.stype = "float16"
        config.l2_normalize = False
        path = store.get_store_path(config)
        expected_path = "/fake/path_20_256_float16_int8_embeddings.npz"
        self.assertEqual(path, expected_path)

        config.norm_type = None
        path = store.get_store_path(config)
        expected_path = "/fake/path_20_256_float16_embeddings.npz"
        self.assertEqual(path, expected_path)


if __name__ == "__main__":
    unittest.main()
