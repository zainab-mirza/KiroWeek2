"""Demo server for Email Summarizer - runs without full dependencies."""

import json
from datetime import datetime

from flask import Flask, jsonify, render_template, request

app = Flask(__name__, template_folder="email_summarizer/web/templates")

# Demo data
DEMO_SUMMARIES = [
    {
        "message_id": "demo1",
        "sender": "manager@company.com",
        "subject": "Q4 Budget Review Meeting",
        "received_at": "2025-12-07T10:30:00",
        "summary": "Manager requests updated Q4 budget numbers and asks for a 1-page summary by Friday. The meeting is scheduled for next week to review the final numbers.",
        "actions": [
            "Review Q4_budget.xlsx and update revenue estimates",
            "Prepare 1-page summary document",
            "Send summary to manager by Friday",
        ],
        "deadlines": ["2025-12-12"],
        "created_at": "2025-12-07T11:00:00",
        "model_used": "gpt-3.5-turbo",
        "feedback": None,
    },
    {
        "message_id": "demo2",
        "sender": "team@project.com",
        "subject": "Sprint Planning - New Features",
        "received_at": "2025-12-07T09:15:00",
        "summary": "Team lead outlines three new features for the upcoming sprint: user authentication, dashboard redesign, and API integration. Requests feedback on priorities.",
        "actions": [
            "Review proposed features list",
            "Provide priority feedback",
            "Attend sprint planning meeting on Monday",
        ],
        "deadlines": ["2025-12-09"],
        "created_at": "2025-12-07T10:45:00",
        "model_used": "gpt-3.5-turbo",
        "feedback": {"rating": 1, "comment": None, "created_at": "2025-12-07T11:30:00"},
    },
    {
        "message_id": "demo3",
        "sender": "hr@company.com",
        "subject": "Annual Performance Review",
        "received_at": "2025-12-06T14:20:00",
        "summary": "HR department reminds about the upcoming annual performance review cycle. Self-assessment forms need to be completed and submitted through the portal.",
        "actions": [
            "Complete self-assessment form",
            "Submit through HR portal",
            "Schedule 1-on-1 with manager",
        ],
        "deadlines": ["2025-12-15"],
        "created_at": "2025-12-07T10:00:00",
        "model_used": "gpt-3.5-turbo",
        "feedback": None,
    },
    {
        "message_id": "demo4",
        "sender": "client@external.com",
        "subject": "Project Deliverables Update",
        "received_at": "2025-12-06T11:45:00",
        "summary": "Client requests status update on project deliverables and asks about timeline for the next milestone. They also want to schedule a call to discuss requirements.",
        "actions": [
            "Prepare status update document",
            "Update project timeline",
            "Schedule call with client",
        ],
        "deadlines": ["2025-12-10"],
        "created_at": "2025-12-07T09:30:00",
        "model_used": "gpt-3.5-turbo",
        "feedback": None,
    },
    {
        "message_id": "demo5",
        "sender": "newsletter@tech.com",
        "subject": "Weekly Tech Digest",
        "received_at": "2025-12-06T08:00:00",
        "summary": "Weekly newsletter covering latest tech trends, including AI developments, new programming frameworks, and industry news. No action required.",
        "actions": [],
        "deadlines": [],
        "created_at": "2025-12-07T09:00:00",
        "model_used": "gpt-3.5-turbo",
        "feedback": None,
    },
]


@app.route("/")
def index():
    """Serve digest homepage."""
    return render_template("digest.html")


@app.route("/api/summaries", methods=["GET"])
def list_summaries():
    """List all email summaries."""
    return jsonify(DEMO_SUMMARIES)


@app.route("/api/summaries/<message_id>", methods=["GET"])
def get_summary(message_id):
    """Get single email summary."""
    for summary in DEMO_SUMMARIES:
        if summary["message_id"] == message_id:
            return jsonify(summary)
    return jsonify({"error": "Summary not found"}), 404


@app.route("/api/summaries/<message_id>/feedback", methods=["POST"])
def submit_feedback(message_id):
    """Submit feedback for a summary."""
    data = request.get_json()

    for summary in DEMO_SUMMARIES:
        if summary["message_id"] == message_id:
            summary["feedback"] = {
                "rating": data["rating"],
                "comment": data.get("comment"),
                "created_at": datetime.now().isoformat(),
            }
            return jsonify({"success": True})

    return jsonify({"error": "Summary not found"}), 404


@app.route("/api/process", methods=["POST"])
def process_emails():
    """Trigger email processing (demo mode)."""
    data = request.get_json() or {}
    dry_run = data.get("dry_run", False)

    return jsonify(
        {
            "total_fetched": 5,
            "total_processed": 5,
            "total_failed": 0,
            "dry_run": dry_run,
            "errors": [],
            "message": "Demo mode: Showing sample summaries. Run full setup to process real emails.",
        }
    )


@app.route("/api/authorize", methods=["POST"])
def initiate_auth():
    """Initiate OAuth flow (demo mode)."""
    return jsonify(
        {
            "message": "Demo mode: OAuth not configured. Run setup wizard to configure real email access.",
            "auth_url": "#",
        }
    )


@app.route("/api/data", methods=["DELETE"])
def erase_data():
    """Erase all data (demo mode)."""
    return jsonify({"success": True, "message": "Demo mode: No real data to erase."})


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify(
        {"status": "healthy", "mode": "demo", "timestamp": datetime.now().isoformat()}
    )


@app.route("/consent", methods=["GET"])
def consent_page():
    """Serve consent page."""
    return render_template("consent.html")


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Email Summarizer - DEMO MODE")
    print("=" * 60)
    print()
    print("✨ The demo server is starting with sample data...")
    print()
    print("📧 Features you can try:")
    print("   • View 5 sample email summaries")
    print("   • Filter and search summaries")
    print("   • Provide feedback (thumbs up/down)")
    print("   • See the beautiful UI in action")
    print()
    print("🔧 To use with real emails:")
    print("   1. Wait for pip installation to complete")
    print("   2. Run: python -m email_summarizer setup")
    print("   3. Configure OAuth credentials")
    print("   4. Run: python -m email_summarizer serve")
    print()
    print("=" * 60)
    print("🌐 Opening: http://localhost:8080")
    print("=" * 60)
    print()

    app.run(host="localhost", port=8080, debug=False)
