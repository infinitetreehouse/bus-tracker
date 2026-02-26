# 1) stdlib
import os
from logging.config import fileConfig

# 2) third-party
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool
from alembic import context

# 3) app (lightweight only)
from bustracker.config import DevConfig, ProdConfig
from bustracker.models.base import Base
import bustracker.models

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
# target_metadata = None
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_url():
    """
    Added our own helper to get the database URL.
    """
    load_dotenv()
    env = os.getenv('FLASK_ENV', 'development').lower()
    cfg = ProdConfig() if env == 'production' else DevConfig()
    return cfg.MIGRATE_DATABASE_URI


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    
    # Updated 2/17/2026, commented out default to use new helper function
    # url = config.get_main_option("sqlalchemy.url")
    url = get_url()
    
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={'paramstyle': 'named'},
        
        # Added 2/17/2026, was not included by default
        compare_type=True,
        compare_server_default=True
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    
    # Updated 2/17/2026, to use new helper function
    config.set_main_option('sqlalchemy.url', get_url())
    
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            
            # Added 2/17/2026, was not included by default
            compare_type=True,
            compare_server_default=True
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
