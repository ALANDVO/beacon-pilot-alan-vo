"""Conftest for backend tests."""
import pytest
import pytest_asyncio
import sys
import tempfile
import os
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import ASGITransport, AsyncClient

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import Database
from app.models.memory import Base  # This imports the models
from app.core.config import Settings, get_settings

# Use a temporary file-based database for testing
# :memory: doesn't work well with async sqlite across connections


@pytest.fixture(scope="function")
def test_db_path():
    """Create a temporary database file path for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    print(f"[DEBUG] Created test DB at: {db_path}", file=sys.stderr)
    yield db_path
    # Cleanup
    try:
        os.unlink(db_path)
        print(f"[DEBUG] Deleted test DB: {db_path}", file=sys.stderr)
    except OSError:
        pass


@pytest.fixture(scope="function")
def test_settings(test_db_path):
    """Override settings for testing."""
    # Clear the lru_cache
    get_settings.cache_clear()
    db_url = f"sqlite+aiosqlite:///{test_db_path}"
    print(f"[DEBUG] Test settings DB URL: {db_url}", file=sys.stderr)
    return Settings(
        database_url=db_url,
        debug=True,
        environment="test",
        secret_key="test-secret",
        oidc_enabled=False,
    )


@pytest_asyncio.fixture(scope="function")
async def test_db(test_settings):
    """Create a test database."""
    print(f"[DEBUG] test_db fixture: creating Database with URL: {test_settings.database_url}", file=sys.stderr)
    db = Database(test_settings.database_url)
    print(f"[DEBUG] test_db fixture: calling create_all", file=sys.stderr)
    # Models are already imported via "from app.models.memory import Base" above
    await db.create_all()
    print(f"[DEBUG] test_db fixture: create_all done, yielding db", file=sys.stderr)
    yield db
    print(f"[DEBUG] test_db fixture: closing db", file=sys.stderr)
    await db.close()
    print(f"[DEBUG] test_db fixture: db closed", file=sys.stderr)


@pytest_asyncio.fixture(scope="function")
async def test_session(test_db) -> AsyncSession:
    """Get a test database session."""
    async with test_db.session() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(test_db, test_settings):
    """Create test client with overridden database and settings."""
    print(f"[DEBUG] client fixture: overriding global _db", file=sys.stderr)
    # Override the global database in the CORRECT module (app.core.database, not backend.app.core.database)
    import app.core.database as db_module
    original_db = db_module._db
    db_module._db = test_db
    
    # Clear settings cache and monkey patch get_settings
    get_settings.cache_clear()
    import app.core.config as config_module
    original_get_settings = config_module.get_settings
    config_module.get_settings = lambda: test_settings
    
    # Import create_app AFTER patching settings
    from app.main import create_app
    app = create_app()
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        print(f"[DEBUG] client fixture: yielding client", file=sys.stderr)
        yield ac
    
    print(f"[DEBUG] client fixture: restoring globals", file=sys.stderr)
    # Restore
    db_module._db = original_db
    config_module.get_settings = original_get_settings
    get_settings.cache_clear()