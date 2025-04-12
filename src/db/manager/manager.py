from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
    AsyncEngine,
)

import logging

from src.settings.db import rdb_settings


# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DBManager:
    engine: AsyncEngine | None = None
    async_session: async_sessionmaker[AsyncSession] | None = None

    def create_engine(self):
        """Create an async engine."""
        logger.info("Creating database engine...")
        self.engine = create_async_engine(rdb_settings.DATABASE_URL, echo=True)

    def create_async_session_maker(self):
        """Create an async session factory."""
        if self.engine is None:
            raise RuntimeError("Database engine is not initialized")

        logger.info("Creating async session maker...")

        self.async_session = async_sessionmaker(
            bind=self.engine, class_=AsyncSession, expire_on_commit=False
        )

    def init_db(self):
        """Initialize the database engine and session maker."""
        logger.info("Initializing database connection...")

        self.create_engine()
        self.create_async_session_maker()

        logger.info("Database successfully initialized.")

    async def close_db(self):
        """Dispose of the database engine."""
        if self.engine is not None:
            logger.info("Disposing database engine...")

            await self.engine.dispose()
            self.engine = None
            self.async_session = None
            logger.info("Database connection successfully closed.")

    async def get_db_session(self):
        """Dependency function to get a database session."""
        if self.async_session is None:
            raise RuntimeError("Database session factory is not initialized")
        async with self.async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise e
            finally:
                await session.close()


db_manager = DBManager()
