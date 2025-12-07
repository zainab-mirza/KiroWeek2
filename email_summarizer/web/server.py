"""Flask web server for Email Summarizer."""

import logging
from pathlib import Path
from flask import Flask, render_template, jsonify, request, redirect
from datetime import datetime
from email_summarizer.models import Feedback
from email_summarizer.orchestrator import EmailOrchestrator
from email_summarizer.storage import StorageManager
from email_summarizer.auth import OAuthAuthenticator

logger = logging.getLogger(__name__)


def create_app(
    orchestrator: EmailOrchestrator,
    storage: StorageManager,
    authenticator: OAuthAuthenticator,
    config,
) -> Flask:
    """Create and configure Flask application.

    Args:
        orchestrator: Email orchestrator instance
        storage: Storage manager instance
        authenticator: OAuth authenticator instance
        config: Application configuration

    Returns:
        Configured Flask app
    """
    app = Flask(__name__, template_folder="templates")
    app.config["SECRET_KEY"] = "dev-secret-key-change-in-production"

    @app.route("/")
    def index():
        """Serve digest homepage."""
        return render_template("digest.html")

    @app.route("/oauth2callback")
    def oauth_callback():
        """Handle OAuth callback."""
        try:
            code = request.args.get("code")
            if not code:
                return jsonify({"error": "No authorization code provided"}), 400

            # Exchange code for credentials
            credentials = authenticator.handle_callback(code)

            return redirect("/?auth=success")

        except Exception as e:
            logger.error(f"OAuth callback error: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/summaries", methods=["GET"])
    def list_summaries():
        """List all email summaries."""
        try:
            limit = request.args.get("limit", type=int)
            offset = request.args.get("offset", default=0, type=int)

            summaries = storage.list_summaries(limit=limit, offset=offset)

            # Convert to dict for JSON serialization
            summaries_data = []
            for summary in summaries:
                data = {
                    "message_id": summary.message_id,
                    "sender": summary.sender,
                    "subject": summary.subject,
                    "received_at": summary.received_at.isoformat(),
                    "summary": summary.summary,
                    "actions": summary.actions,
                    "deadlines": [d.isoformat() for d in summary.deadlines],
                    "created_at": summary.created_at.isoformat(),
                    "model_used": summary.model_used,
                }

                if summary.feedback:
                    data["feedback"] = {
                        "rating": summary.feedback.rating,
                        "comment": summary.feedback.comment,
                        "created_at": summary.feedback.created_at.isoformat(),
                    }

                summaries_data.append(data)

            return jsonify(summaries_data)

        except Exception as e:
            logger.error(f"Error listing summaries: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/summaries/<message_id>", methods=["GET"])
    def get_summary(message_id: str):
        """Get single email summary."""
        try:
            summary = storage.get_summary(message_id)

            if not summary:
                return jsonify({"error": "Summary not found"}), 404

            data = {
                "message_id": summary.message_id,
                "sender": summary.sender,
                "subject": summary.subject,
                "received_at": summary.received_at.isoformat(),
                "summary": summary.summary,
                "actions": summary.actions,
                "deadlines": [d.isoformat() for d in summary.deadlines],
                "created_at": summary.created_at.isoformat(),
                "model_used": summary.model_used,
            }

            if summary.feedback:
                data["feedback"] = {
                    "rating": summary.feedback.rating,
                    "comment": summary.feedback.comment,
                    "created_at": summary.feedback.created_at.isoformat(),
                }

            return jsonify(data)

        except Exception as e:
            logger.error(f"Error getting summary: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/summaries/<message_id>/feedback", methods=["POST"])
    def submit_feedback(message_id: str):
        """Submit feedback for a summary."""
        try:
            data = request.get_json()

            if "rating" not in data:
                return jsonify({"error": "Rating is required"}), 400

            rating = data["rating"]
            if rating not in [1, -1]:
                return jsonify({"error": "Rating must be 1 or -1"}), 400

            feedback = Feedback(
                rating=rating, comment=data.get("comment"), created_at=datetime.now()
            )

            storage.save_feedback(message_id, feedback)

            return jsonify({"success": True})

        except Exception as e:
            logger.error(f"Error submitting feedback: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/process", methods=["POST"])
    def process_emails():
        """Trigger email processing."""
        try:
            data = request.get_json() or {}
            dry_run = data.get("dry_run", False)

            logger.info(f"Processing emails (dry_run={dry_run})")
            result = orchestrator.process_emails(dry_run=dry_run)

            return jsonify(
                {
                    "total_fetched": result.total_fetched,
                    "total_processed": result.total_processed,
                    "total_failed": result.total_failed,
                    "dry_run": result.dry_run,
                    "errors": [
                        {
                            "message_id": e.message_id,
                            "error_type": e.error_type,
                            "error_message": e.error_message,
                        }
                        for e in result.errors
                    ],
                }
            )

        except Exception as e:
            logger.error(f"Error processing emails: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/authorize", methods=["POST"])
    def initiate_auth():
        """Initiate OAuth flow."""
        try:
            auth_url = authenticator.get_authorization_url()
            return jsonify({"auth_url": auth_url})

        except Exception as e:
            logger.error(f"Error initiating auth: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/data", methods=["DELETE"])
    def erase_data():
        """Erase all data."""
        try:
            storage.delete_all()
            return jsonify({"success": True})

        except Exception as e:
            logger.error(f"Error erasing data: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/config", methods=["GET"])
    def config_page():
        """Serve configuration page."""
        # TODO: Implement configuration UI
        return jsonify({"message": "Configuration UI not yet implemented"})

    @app.route("/api/config", methods=["POST"])
    def update_config():
        """Update configuration."""
        # TODO: Implement configuration update
        return jsonify({"message": "Configuration update not yet implemented"})

    @app.route("/consent", methods=["GET"])
    def consent_page():
        """Serve consent page."""
        return render_template("consent.html")

    @app.route("/api/consent", methods=["POST"])
    def save_consent():
        """Save user consent for remote LLM."""
        try:
            data = request.get_json()
            consent = data.get("consent", False)

            # Update config
            from email_summarizer.config import ConfigManager

            config_manager = ConfigManager()
            current_config = config_manager.load_config()
            current_config.privacy.remote_llm_consent = consent
            config_manager.save_config(current_config)

            return jsonify({"success": True})

        except Exception as e:
            logger.error(f"Error saving consent: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/health", methods=["GET"])
    def health_check():
        """Health check endpoint."""
        return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

    return app


def run_server(
    orchestrator: EmailOrchestrator,
    storage: StorageManager,
    authenticator: OAuthAuthenticator,
    config,
    host: str = "localhost",
    port: int = 8080,
) -> None:
    """Run the Flask web server.

    Args:
        orchestrator: Email orchestrator instance
        storage: Storage manager instance
        authenticator: OAuth authenticator instance
        config: Application configuration
        host: Server host
        port: Server port
    """
    app = create_app(orchestrator, storage, authenticator, config)

    logger.info(f"Starting web server on http://{host}:{port}")
    app.run(host=host, port=port, debug=False)
