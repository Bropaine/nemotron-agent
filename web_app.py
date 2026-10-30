from threading import Lock

from flask import Flask, jsonify, render_template, request

from agent import run_agent

from discovery_store import initialize_database, save_rating, validate_feedback

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 8192
app.config["TRUSTED_HOSTS"] = ["127.0.0.1", "localhost"]
agent_lock = Lock()


@app.get("/")
def home():
    return render_template("index.html")


def get_interest(data) -> str:
    if not isinstance(data, dict):
        raise ValueError("Send a JSON object containing an interest.")
    interest = data.get("interest")
    if not isinstance(interest, str):
        raise ValueError("Interest must be text.")
    interest = interest.strip()
    if not 1 <= len(interest) <= 500:
        raise ValueError("Enter an interest between 1 and 500 characters.")
    return interest


def discover(interest: str) -> dict:
    agent_request = (
            "Find one interesting, informative page about this interest: "
            + interest
            + "\nSearch for candidates and read a suitable page before recommending it. "
              "Use the returned content as evidence. Do not recommend a previously saved page."
    )
    return run_agent(agent_request)


@app.post("/api/stumble")
def stumble():
    origin = request.headers.get("Origin")
    if origin is not None and origin != request.host_url.rstrip("/"):
        return jsonify(status="error", message="Cross-origin requests are not allowed."), 403
    if not request.is_json:
        return jsonify(status="error", message="Send application/json."), 415

    try:
        interest = get_interest(request.get_json(silent=True))
    except ValueError as error:
        return jsonify(status="error", message=str(error)), 400

    if not agent_lock.acquire(blocking=False):
        return jsonify(status="busy", message="A discovery is already running."), 409
    try:
        return jsonify(discover(interest))
    except Exception:
        app.logger.exception("Discovery failed")
        return jsonify(status="error", message="Discovery failed. Check the server terminal."), 500
    finally:
        agent_lock.release()


def get_rating_input(data) -> tuple[str, int, str, str]:
    if not isinstance(data, dict):
        raise ValueError("Send a JSON object containing url and value.")
    url = data.get("url")
    value = data.get("value")
    if not isinstance(url, str) or not url.strip():
        raise ValueError("A recommendation URL is required.")
    if type(value) is not int or value not in (-1, 1):
        raise ValueError("Rating must be +1 or -1.")

    reason, note = validate_feedback(
        data.get("feedback_reason", ""),
        data.get("feedback_note", ""),
    )
    return url.strip(), value, reason, note


@app.post("/api/rating")
def rate_recommendation():
    origin = request.headers.get("Origin")
    if origin is not None and origin != request.host_url.rstrip("/"):
        return jsonify(status="error", message="Cross-origin requests are not allowed."), 403
    if not request.is_json:
        return jsonify(status="error", message="Send application/json."), 415

    try:
        url, value, reason, note = get_rating_input(request.get_json(silent=True))
    except ValueError as error:
        return jsonify(status="error", message=str(error)), 400

    try:
        initialize_database()
        saved = save_rating(url, value, reason, note)
    except Exception:
        app.logger.exception("Saving rating failed")
        return jsonify(status="error", message="Could not save rating."), 500

    if not saved:
        return jsonify(status="error", message="Recommendation not found."), 404
    return jsonify(
        status="rated",
        url=url,
        value=value,
        feedback_reason=reason,
        feedback_note=note,
        )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)