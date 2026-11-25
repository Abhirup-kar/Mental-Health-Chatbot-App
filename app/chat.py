"""Chat, sentiment analytics, and video recommendation blueprint."""

from __future__ import annotations

from typing import Any

from flask import Blueprint, current_app, g, jsonify, render_template, request

from app.auth import login_required
from shared.sentiment_engine import analyze_communication_pattern

chat_bp = Blueprint("chat", __name__)


def _derive_session_title(message: str) -> str:
    cleaned = " ".join(message.strip().split())
    if len(cleaned) <= 42:
        return cleaned or "New Check-In"
    return cleaned[:39].rstrip() + "..."


def _build_analytics_payload(
    logs: list[dict[str, Any]],
) -> dict[str, Any]:
    pattern = analyze_communication_pattern(logs)
    timeline = [
        {
            "index": idx + 1,
            "sentiment": item["sentiment"],
            "score": float(item["score"]),
            "emotion": item["emotion"],
            "created_at": item.get("created_at"),
        }
        for idx, item in enumerate(logs[-20:])
    ]
    return {
        "summary": pattern,
        "timeline": timeline,
    }


@chat_bp.route("/chat")
@login_required
def chat_page() -> Any:
    db = current_app.extensions["db"]
    rasa_client = current_app.extensions["rasa_client"]
    sessions = db.get_user_sessions(g.user["id"])
    videos = db.list_videos()
    return render_template(
        "chat.html",
        user=g.user,
        sessions=sessions,
        initial_videos=videos,
        db_backend=db.backend,
        rasa_connected=rasa_client.check_health(),
    )


@chat_bp.route("/api/health", methods=["GET"])
def api_health() -> Any:
    db = current_app.extensions["db"]
    rasa_client = current_app.extensions["rasa_client"]
    return jsonify(
        {
            "status": "ok",
            "database_backend": db.backend,
            "rasa_connected": rasa_client.check_health(),
        }
    )


@chat_bp.route("/api/sessions", methods=["GET", "POST"])
@login_required
def api_sessions() -> Any:
    db = current_app.extensions["db"]
    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        title = str(payload.get("title") or "New Check-In").strip() or "New Check-In"
        created = db.create_session(g.user["id"], title=title)
        created["created_at"] = str(created["created_at"])
        created["updated_at"] = str(created["updated_at"])
        return jsonify({"session": created}), 201

    rows = db.get_user_sessions(g.user["id"])
    for row in rows:
        row["created_at"] = str(row["created_at"])
        row["updated_at"] = str(row["updated_at"])
    return jsonify({"sessions": rows})


@chat_bp.route("/api/sessions/<int:session_id>", methods=["DELETE"])
@login_required
def api_delete_session(session_id: int) -> Any:
    db = current_app.extensions["db"]
    deleted = db.delete_session(session_id, g.user["id"])
    if not deleted:
        return jsonify({"error": "Session not found."}), 404
    return jsonify({"deleted": True, "session_id": session_id})


@chat_bp.route("/api/sessions/<int:session_id>/messages", methods=["GET"])
@login_required
def api_session_messages(session_id: int) -> Any:
    db = current_app.extensions["db"]
    chat_session = db.get_session(session_id, g.user["id"])
    if chat_session is None:
        return jsonify({"error": "Session not found."}), 404

    messages = db.get_session_messages(session_id, g.user["id"])
    logs = db.get_user_sentiment_logs(g.user["id"], session_id=session_id)
    chat_session["created_at"] = str(chat_session["created_at"])
    chat_session["updated_at"] = str(chat_session["updated_at"])
    return jsonify(
        {
            "session": chat_session,
            "messages": messages,
            "analytics": _build_analytics_payload(logs),
        }
    )


@chat_bp.route("/api/chat", methods=["POST"])
@login_required
def api_chat() -> Any:
    payload = request.get_json(silent=True) or {}
    raw_message = str(payload.get("message") or "").strip()
    if not raw_message:
        return jsonify({"error": "Please enter a message before sending."}), 400
    if len(raw_message) > 2000:
        return jsonify({"error": "Message must be 2000 characters or fewer."}), 400

    db = current_app.extensions["db"]
    rasa_client = current_app.extensions["rasa_client"]
    user_id = int(g.user["id"])

    requested_session_id = payload.get("session_id")
    if requested_session_id is not None:
        chat_session = db.get_session(int(requested_session_id), user_id)
        if chat_session is None:
            return jsonify({"error": "Chat session not found."}), 404
    else:
        chat_session = db.create_session(user_id, title="New Check-In")

    session_id = int(chat_session["id"])
    prior_logs = db.get_user_sentiment_logs(user_id, session_id=session_id, limit=50)
    recent_video_ids = db.get_session_recent_video_ids(session_id, user_id)

    rasa_result = rasa_client.send_message(
        sender_id=f"user_{user_id}_session_{session_id}",
        message=raw_message,
        recent_history=prior_logs,
    )

    current_analysis = {
        "sentiment": rasa_result["sentiment"],
        "score": float(rasa_result["score"]),
        "confidence": float(rasa_result["confidence"]),
        "emotion": rasa_result["emotion"],
        "is_crisis": bool(rasa_result["is_crisis"]),
        "should_recommend_videos": bool(rasa_result["should_recommend_videos"]),
        "intent": rasa_result["intent"],
        "intent_confidence": float(rasa_result["intent_confidence"]),
    }

    updated_history = list(prior_logs)
    if current_analysis["should_recommend_videos"]:
        updated_history.append(current_analysis)
    pattern = analyze_communication_pattern(updated_history)

    recommended_videos: list[dict[str, Any]] = []
    if current_analysis["should_recommend_videos"]:
        video_limit = 3 if pattern["consecutive_negative"] >= 3 else 2
        recommended_videos = db.get_recommended_videos(
            sentiment=current_analysis["sentiment"],
            emotion=current_analysis["emotion"],
            exclude_ids=recent_video_ids,
            limit=video_limit,
        )

    user_msg_id = db.add_message(
        session_id=session_id,
        user_id=user_id,
        sender="user",
        message_text=raw_message,
        sentiment=current_analysis["sentiment"],
        sentiment_score=current_analysis["score"],
        emotion=current_analysis["emotion"],
        detected_intent=current_analysis["intent"],
        engine_used=rasa_result["engine_used"],
    )

    if current_analysis["should_recommend_videos"]:
        db.add_sentiment_log(
            user_id=user_id,
            session_id=session_id,
            message_id=user_msg_id,
            sentiment=current_analysis["sentiment"],
            score=current_analysis["score"],
            emotion=current_analysis["emotion"],
            pattern_trend=pattern["trend"],
        )

    video_ids = [int(v["id"]) for v in recommended_videos]
    bot_msg_id = db.add_message(
        session_id=session_id,
        user_id=user_id,
        sender="bot",
        message_text=rasa_result["reply_text"],
        sentiment=current_analysis["sentiment"],
        sentiment_score=current_analysis["score"],
        emotion=current_analysis["emotion"],
        detected_intent=current_analysis["intent"],
        engine_used=rasa_result["engine_used"],
        recommended_video_ids=video_ids,
    )

    session_title = chat_session["title"]
    if session_title == "New Check-In" and len(raw_message.split()) >= 2:
        session_title = _derive_session_title(raw_message)
        db.update_session_title(session_id, session_title)

    return jsonify(
        {
            "session_id": session_id,
            "session_title": session_title,
            "user_message": {
                "id": user_msg_id,
                "sender": "user",
                "message_text": raw_message,
                "sentiment": current_analysis["sentiment"],
                "sentiment_score": current_analysis["score"],
                "emotion": current_analysis["emotion"],
                "detected_intent": current_analysis["intent"],
            },
            "bot_message": {
                "id": bot_msg_id,
                "sender": "bot",
                "message_text": rasa_result["reply_text"],
                "sentiment": current_analysis["sentiment"],
                "sentiment_score": current_analysis["score"],
                "emotion": current_analysis["emotion"],
                "detected_intent": current_analysis["intent"],
                "engine_used": rasa_result["engine_used"],
                "videos": recommended_videos,
            },
            "analysis": current_analysis,
            "pattern": pattern,
            "videos": recommended_videos,
            "engine_used": rasa_result["engine_used"],
        }
    )


@chat_bp.route("/api/analytics", methods=["GET"])
@login_required
def api_analytics() -> Any:
    db = current_app.extensions["db"]
    session_param = request.args.get("session_id")
    session_id = int(session_param) if session_param and session_param.isdigit() else None
    logs = db.get_user_sentiment_logs(g.user["id"], session_id=session_id, limit=100)
    return jsonify(_build_analytics_payload(logs))


@chat_bp.route("/api/videos", methods=["GET"])
@login_required
def api_videos() -> Any:
    db = current_app.extensions["db"]
    sentiment = request.args.get("sentiment")
    videos = db.list_videos(sentiment=sentiment)
    return jsonify({"videos": videos})
