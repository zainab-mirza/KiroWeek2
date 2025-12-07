"""Command-line interface for Email Summarizer."""

import argparse
import sys
from pathlib import Path

from email_summarizer.auth import create_authenticator
from email_summarizer.config import ConfigManager
from email_summarizer.fetcher import create_fetcher
from email_summarizer.orchestrator import EmailOrchestrator
from email_summarizer.preprocessor import EmailPreprocessor
from email_summarizer.storage import StorageManager
from email_summarizer.summarizer import create_summarizer
from email_summarizer.utils.logging_config import setup_logging
from email_summarizer.web import run_server


def setup_wizard():
    """Interactive setup wizard."""
    print("=" * 60)
    print("Email Summarizer - Setup Wizard")
    print("=" * 60)
    print()

    config_manager = ConfigManager()

    # Email provider
    print("1. Email Provider")
    print("   a) Gmail")
    print("   b) Outlook/Office365")
    provider_choice = input("Select provider (a/b): ").strip().lower()

    provider = "gmail" if provider_choice == "a" else "outlook"

    # Create default config
    config = config_manager.create_default_config(provider)

    # OAuth credentials
    print("\n2. OAuth Credentials")
    print(f"   You need to register an OAuth app for {provider}")
    if provider == "gmail":
        print("   Visit: https://console.cloud.google.com/apis/credentials")
    else:
        print("   Visit: https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps")

    client_id = input("   Enter Client ID: ").strip()
    client_secret = input("   Enter Client Secret: ").strip()

    # Store in keyring
    config_manager.set_secret("oauth_client_id", client_id)
    config_manager.set_secret("oauth_client_secret", client_secret)

    # Summarizer choice
    print("\n3. Summarizer Engine")
    print("   a) Remote LLM (OpenAI) - Higher quality, requires API key")
    print("   b) Local Model - Fully private, slower")
    summarizer_choice = input("Select engine (a/b): ").strip().lower()

    if summarizer_choice == "a":
        config.summarizer.engine = "remote"
        api_key = input("   Enter OpenAI API key: ").strip()
        config_manager.set_secret("openai_api_key", api_key)
    else:
        config.summarizer.engine = "local"
        model = input(
            "   Enter model name (default: facebook/bart-large-cnn): "
        ).strip()
        if model:
            config.summarizer.local_model = model

    # Server port
    print("\n4. Server Configuration")
    port_input = input(f"   Enter port (default: {config.server.port}): ").strip()
    if port_input:
        config.server.port = int(port_input)

    # Save configuration
    config_manager.save_config(config)

    print("\n" + "=" * 60)
    print("Setup complete!")
    print(f"Configuration saved to: {config_manager.config_path}")
    print("\nNext steps:")
    print("  1. Run 'python -m email_summarizer serve' to start the server")
    print("  2. Visit http://localhost:{} in your browser".format(config.server.port))
    print("  3. Click 'Authorize' to connect your email account")
    print("=" * 60)


def serve_command(args):
    """Start the web server."""
    config_manager = ConfigManager()

    try:
        config = config_manager.load_config()
    except FileNotFoundError:
        print("Error: Configuration not found. Run 'setup' first.")
        sys.exit(1)

    # Setup logging
    log_dir = Path.home() / ".email-summarizer" / "logs"
    setup_logging(log_dir, config.privacy.log_rotation_days)

    # Get secrets
    try:
        client_id = config_manager.resolve_secret_ref(config.oauth.client_id_ref)
        client_secret = config_manager.resolve_secret_ref(
            config.oauth.client_secret_ref
        )
    except KeyError as e:
        print(f"Error: Missing secret: {e}")
        print("Run 'setup' to configure credentials.")
        sys.exit(1)

    # Create components
    token_file = Path.home() / ".email-summarizer" / "tokens.enc"
    authenticator = create_authenticator(
        config.email_provider, config.oauth, client_id, client_secret, token_file
    )

    # Load credentials
    credentials = authenticator.load_credentials()
    if not credentials:
        print("Warning: Not authenticated. Visit the web UI to authorize.")
        # Create dummy components for now
        fetcher = None
        orchestrator = None
    else:
        # Check if token needs refresh
        if credentials.is_expired():
            print("Refreshing expired token...")
            credentials = authenticator.refresh_token(credentials)

        fetcher = create_fetcher(config.email_provider, credentials)
        preprocessor = EmailPreprocessor()

        # Create summarizer
        if config.summarizer.engine == "remote":
            api_key = config_manager.resolve_secret_ref(
                config.summarizer.remote_api_key_ref
            )
            summarizer = create_summarizer(
                "remote",
                provider=config.summarizer.remote_provider,
                api_key=api_key,
                max_tokens=config.summarizer.max_input_tokens,
            )
        else:
            summarizer = create_summarizer(
                "local",
                model_name=config.summarizer.local_model,
                max_tokens=config.summarizer.max_input_tokens,
            )

        storage = StorageManager(config.storage)

        orchestrator = EmailOrchestrator(
            config, fetcher, preprocessor, summarizer, storage
        )

    # Create minimal components for unauthenticated state
    if not orchestrator:
        storage = StorageManager(config.storage)
        orchestrator = None  # Will handle in server

    # Run server
    run_server(
        orchestrator,
        storage,
        authenticator,
        config,
        host=config.server.host,
        port=config.server.port,
    )


def process_command(args):
    """Process emails from CLI."""
    config_manager = ConfigManager()

    try:
        config = config_manager.load_config()
    except FileNotFoundError:
        print("Error: Configuration not found. Run 'setup' first.")
        sys.exit(1)

    # Setup logging
    log_dir = Path.home() / ".email-summarizer" / "logs"
    setup_logging(log_dir, config.privacy.log_rotation_days)

    # Get secrets and create components (similar to serve_command)
    # ... (implementation similar to serve_command)

    print("Processing emails...")
    # result = orchestrator.process_emails(dry_run=args.dry_run)
    # print(f"Processed {result.total_processed}/{result.total_fetched} emails")


def erase_command(args):
    """Erase all data."""
    if not args.confirm:
        response = input("Are you sure you want to erase all data? (yes/no): ")
        if response.lower() != "yes":
            print("Cancelled.")
            return

    config_manager = ConfigManager()

    try:
        config = config_manager.load_config()
    except FileNotFoundError:
        print("Error: Configuration not found.")
        sys.exit(1)

    storage = StorageManager(config.storage)
    storage.delete_all()

    print("All data erased.")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Email Summarizer - AI-powered email triage"
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Setup command
    subparsers.add_parser("setup", help="Run setup wizard")

    # Serve command
    subparsers.add_parser("serve", help="Start web server")

    # Process command
    process_parser = subparsers.add_parser("process", help="Process emails")
    process_parser.add_argument(
        "--dry-run", action="store_true", help="Preview without saving"
    )

    # Erase command
    erase_parser = subparsers.add_parser("erase", help="Erase all data")
    erase_parser.add_argument(
        "--confirm", action="store_true", help="Skip confirmation prompt"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "setup":
        setup_wizard()
    elif args.command == "serve":
        serve_command(args)
    elif args.command == "process":
        process_command(args)
    elif args.command == "erase":
        erase_command(args)


if __name__ == "__main__":
    main()
