"""Command-line interface for managing API keys."""

import sys

import click

from .key_manager import KeyStorage, SecureKeyManager
from .utils import migrate_from_env


@click.group()
def cli():
    """SocialMapper API key management."""


@cli.command()
@click.argument("key_name")
@click.argument("key_value")
@click.option(
    "--storage",
    type=click.Choice(["keyring", "encrypted", "environment"]),
    help="Storage backend to use"
)
def set(key_name: str, key_value: str, storage: str | None):
    """Store an API key securely."""
    manager = SecureKeyManager()

    # Map string to enum
    storage_map = {
        "keyring": KeyStorage.KEYRING,
        "encrypted": KeyStorage.ENCRYPTED_FILE,
        "environment": KeyStorage.ENVIRONMENT,
    }
    storage_enum = storage_map.get(storage) if storage else None

    if manager.set_key(key_name, key_value, storage_enum):
        click.echo(f"✅ Successfully stored key '{key_name}'")

        # Validate the key
        if manager.validate_key(key_name, key_value):
            click.echo("✅ Key format validated")
        else:
            click.echo("⚠️  Warning: Key format may be invalid")
    else:
        click.echo(f"❌ Failed to store key '{key_name}'", err=True)
        sys.exit(1)


@cli.command()
@click.argument("key_name")
@click.option("--show", is_flag=True, help="Display the actual key value")
def get(key_name: str, show: bool):
    """Retrieve an API key."""
    manager = SecureKeyManager()
    key = manager.get_key(key_name)

    if key:
        if show:
            click.echo(f"{key_name}: {key}")
        else:
            # Show masked version
            masked = key[:4] + "*" * (len(key) - 8) + key[-4:] if len(key) > 8 else "*" * len(key)
            click.echo(f"{key_name}: {masked}")
            click.echo("Use --show to display the full key")
    else:
        click.echo(f"❌ Key '{key_name}' not found", err=True)
        sys.exit(1)


@cli.command()
@click.argument("key_name")
@click.option("--all", "delete_all", is_flag=True, help="Delete from all storage backends")
def delete(key_name: str, delete_all: bool):
    """Delete an API key."""
    manager = SecureKeyManager()

    storage = None if delete_all else None
    if manager.delete_key(key_name, storage):
        click.echo(f"✅ Successfully deleted key '{key_name}'")
    else:
        click.echo(f"❌ Failed to delete key '{key_name}'", err=True)
        sys.exit(1)


@cli.command()
def list():
    """List all stored keys."""
    manager = SecureKeyManager()
    keys = manager.list_keys()

    if not keys:
        click.echo("No keys found in any storage backend")
        return

    click.echo("Stored API keys:")
    for storage, key_list in keys.items():
        click.echo(f"\n{storage}:")
        for key in key_list:
            click.echo(f"  • {key}")


@cli.command()
def migrate():
    """Migrate keys from environment variables to secure storage."""
    click.echo("Migrating API keys from environment variables...")

    results = migrate_from_env()

    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)

    click.echo(f"\n✅ Migrated {success_count}/{total_count} keys")

    for key_name, success in results.items():
        if success:
            click.echo(f"  ✅ {key_name}")
        else:
            click.echo(f"  ⏭️  {key_name} (not found in environment)")


@cli.command()
@click.argument("key_name")
def validate(key_name: str):
    """Validate an API key."""
    manager = SecureKeyManager()

    key = manager.get_key(key_name)
    if not key:
        click.echo(f"❌ Key '{key_name}' not found", err=True)
        sys.exit(1)

    if manager.validate_key(key_name):
        click.echo(f"✅ Key '{key_name}' appears valid")
    else:
        click.echo(f"❌ Key '{key_name}' appears invalid", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
