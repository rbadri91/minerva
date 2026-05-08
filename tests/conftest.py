import pytest
import tools.memory_tools as mt


@pytest.fixture(autouse=True)
def isolated_chroma(tmp_path):
    """Give each test its own ChromaDB directory and reset the client singleton."""
    original_path = mt._CHROMA_PATH
    original_client = mt._chroma_client

    mt._CHROMA_PATH = str(tmp_path / "chroma_db")
    mt._chroma_client = None

    yield

    mt._chroma_client = None
    mt._CHROMA_PATH = original_path
    mt._chroma_client = original_client
