"""Shared sentiment analysis, communication-pattern tracking, and therapist response engine.

Used by both the Flask backend and the Rasa custom action server so sentiment
scoring, emotion tagging, crisis detection, and video curation remain consistent.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


SEED_VIDEOS: list[dict[str, str]] = [
    {
        "title": "How to practice emotional first aid",
        "channel": "TED (Guy Winch)",
        "youtube_id": "F2hc2FLOdhI",
        "url": "https://www.youtube.com/watch?v=F2hc2FLOdhI",
        "sentiment": "negative",
        "emotion_tag": "sadness",
        "duration_label": "17 min",
        "description": "Psychologist Guy Winch explains practical ways to care for emotional wounds like rejection, loneliness, and rumination.",
    },
    {
        "title": "How to cope with anxiety",
        "channel": "TEDx Talks (Olivia Remes)",
        "youtube_id": "WWloIAQpMcQ",
        "url": "https://www.youtube.com/watch?v=WWloIAQpMcQ",
        "sentiment": "negative",
        "emotion_tag": "anxiety",
        "duration_label": "15 min",
        "description": "Evidence-based coping strategies for regaining control, quieting anxious loops, and finding purpose.",
    },
    {
        "title": "How to Make Anxiety Your Friend",
        "channel": "TED (David H. Rosmarin)",
        "youtube_id": "cTnPqgL8ZPs",
        "url": "https://www.youtube.com/watch?v=cTnPqgL8ZPs",
        "sentiment": "negative",
        "emotion_tag": "anxiety",
        "duration_label": "12 min",
        "description": "Clinical psychologist David H. Rosmarin shares how accepting anxiety can build emotional resilience.",
    },
    {
        "title": "Box breathing relaxation technique: how to calm feelings of stress or anxiety",
        "channel": "Sunnybrook Hospital",
        "youtube_id": "tEmt1Znux58",
        "url": "https://www.youtube.com/watch?v=tEmt1Znux58",
        "sentiment": "negative",
        "emotion_tag": "anxiety",
        "duration_label": "4 min",
        "description": "A quick guided 4-4-4-4 box breathing exercise to calm your nervous system during acute stress or anxiety.",
    },
    {
        "title": "How to Make Stress Your Friend",
        "channel": "TED (Kelly McGonigal)",
        "youtube_id": "RcGyVTAoXEU",
        "url": "https://www.youtube.com/watch?v=RcGyVTAoXEU",
        "sentiment": "negative",
        "emotion_tag": "stress",
        "duration_label": "14 min",
        "description": "Health psychologist Kelly McGonigal shows how reframing stress responses supports resilience and connection.",
    },
    {
        "title": "STRESS BUSTER! - Guided Meditation & Exercise to Release Tension & Stress",
        "channel": "New Horizon",
        "youtube_id": "Poy9UE3xM6w",
        "url": "https://www.youtube.com/watch?v=Poy9UE3xM6w",
        "sentiment": "negative",
        "emotion_tag": "stress",
        "duration_label": "10 min",
        "description": "A soothing guided relaxation and tension-release exercise for unwinding after a demanding day.",
    },
    {
        "title": "Relieve Stress & Anxiety with Simple Breathing Techniques",
        "channel": "AskDoctorJo",
        "youtube_id": "odADwWzHR24",
        "url": "https://www.youtube.com/watch?v=odADwWzHR24",
        "sentiment": "negative",
        "emotion_tag": "anger",
        "duration_label": "7 min",
        "description": "Practical paced-breathing routines to release physical agitation, frustration, and acute tension.",
    },
    {
        "title": "15 Minute Deep Breathing Exercise",
        "channel": "City of Hope",
        "youtube_id": "F28MGLlpP90",
        "url": "https://www.youtube.com/watch?v=F28MGLlpP90",
        "sentiment": "negative",
        "emotion_tag": "sleep",
        "duration_label": "15 min",
        "description": "A gentle 15-minute deep breathing session ideal for easing restlessness and preparing for rest.",
    },
    {
        "title": "All it takes is 10 mindful minutes",
        "channel": "TED (Andy Puddicombe)",
        "youtube_id": "qzR62JJCMBQ",
        "url": "https://www.youtube.com/watch?v=qzR62JJCMBQ",
        "sentiment": "neutral",
        "emotion_tag": "mindfulness",
        "duration_label": "10 min",
        "description": "Mindfulness expert Andy Puddicombe introduces how ten quiet minutes a day can refresh perspective.",
    },
    {
        "title": "Daily Calm | 10 Minute Mindfulness Meditation | Be Present",
        "channel": "Calm",
        "youtube_id": "ZToicYcHIOU",
        "url": "https://www.youtube.com/watch?v=ZToicYcHIOU",
        "sentiment": "neutral",
        "emotion_tag": "mindfulness",
        "duration_label": "10 min",
        "description": "A steady 10-minute guided mindfulness practice focused on breath awareness and staying present.",
    },
    {
        "title": "5-Minute Meditation You Can Do Anywhere",
        "channel": "Goodful",
        "youtube_id": "inpok4MKVLM",
        "url": "https://www.youtube.com/watch?v=inpok4MKVLM",
        "sentiment": "neutral",
        "emotion_tag": "neutral",
        "duration_label": "5 min",
        "description": "A short, accessible five-minute reset for centering yourself anytime during a routine day.",
    },
    {
        "title": "The Power of Vulnerability",
        "channel": "TED (Brené Brown)",
        "youtube_id": "iCvmsMzlF7o",
        "url": "https://www.youtube.com/watch?v=iCvmsMzlF7o",
        "sentiment": "neutral",
        "emotion_tag": "self_reflection",
        "duration_label": "20 min",
        "description": "Researcher Brené Brown explores human connection, authenticity, and reflective self-compassion.",
    },
    {
        "title": "Want to be happy? Be grateful",
        "channel": "TED (David Steindl-Rast)",
        "youtube_id": "UtBsl3j0YRQ",
        "url": "https://www.youtube.com/watch?v=UtBsl3j0YRQ",
        "sentiment": "positive",
        "emotion_tag": "gratitude",
        "duration_label": "14 min",
        "description": "Brother David Steindl-Rast reflects on how slowing down to notice gratitude deepens everyday joy.",
    },
    {
        "title": "The happy secret to better work",
        "channel": "TED (Shawn Achor)",
        "youtube_id": "fLJsdqxnZb0",
        "url": "https://www.youtube.com/watch?v=fLJsdqxnZb0",
        "sentiment": "positive",
        "emotion_tag": "happiness",
        "duration_label": "12 min",
        "description": "Psychologist Shawn Achor shares upbeat research on how positive mindset fuels resilience and creativity.",
    },
    {
        "title": "What Makes a Good Life? Lessons from the Longest Study on Happiness",
        "channel": "TED (Robert Waldinger)",
        "youtube_id": "8KkKuTCFvzI",
        "url": "https://www.youtube.com/watch?v=8KkKuTCFvzI",
        "sentiment": "positive",
        "emotion_tag": "flourishing",
        "duration_label": "13 min",
        "description": "Insights from the Harvard Study of Adult Development on nurturing warm relationships and long-term well-being.",
    },
]

_MENTAL_HEALTH_LEXICON_UPDATES: dict[str, float] = {
    "anxious": -2.3,
    "anxiety": -2.3,
    "panicking": -2.8,
    "panic": -2.6,
    "overwhelmed": -2.4,
    "burnout": -2.5,
    "stressed": -2.1,
    "depressed": -2.9,
    "depression": -2.8,
    "hopeless": -3.1,
    "worthless": -3.1,
    "exhausted": -2.0,
    "insomnia": -2.1,
    "sleepless": -2.0,
    "numb": -1.8,
    "lonely": -2.2,
    "isolated": -2.1,
    "grieving": -2.5,
    "heartbroken": -2.7,
    "scared": -2.0,
    "frustrated": -1.9,
    "irritated": -1.7,
    "crying": -2.2,
    "drained": -2.1,
    "trapped": -2.4,
    "grateful": 2.4,
    "thankful": 2.2,
    "mindful": 1.6,
    "hopeful": 2.1,
    "peaceful": 2.2,
    "calm": 1.7,
    "relieved": 2.1,
    "proud": 2.0,
    "energized": 2.0,
    "optimistic": 2.1,
    "joyful": 2.6,
    "healing": 1.8,
    "resilient": 1.9,
    "motivated": 2.0,
    "relaxed": 1.9,
    "refreshed": 1.9,
    "thriving": 2.4,
    "okay": 0.0,
    "ok": 0.0,
    "alright": 0.1,
    "fine": 0.1,
}

_ANALYZER = SentimentIntensityAnalyzer()
_ANALYZER.lexicon.update(_MENTAL_HEALTH_LEXICON_UPDATES)

_CRISIS_PATTERNS = [
    re.compile(r"\b(kill|harm|hurt|cut|end)\s+(my\s*self|me)\b", re.IGNORECASE),
    re.compile(r"\b(end\s+my\s+life|take\s+my\s+own\s+life|want\s+to\s+die)\b", re.IGNORECASE),
    re.compile(r"\b(suicidal|suicide|self[-\s]?harm)\b", re.IGNORECASE),
    re.compile(r"\b(no\s+reason\s+to\s+live|don'?t\s+want\s+to\s+live|better\s+off\s+dead)\b", re.IGNORECASE),
]

_GREETING_ONLY_PATTERNS = [
    re.compile(
        r"^(hi|hello|hey|hiya|howdy|good\s+(morning|afternoon|evening)|greetings|yo|sup)[\s!.,?]*$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^(bye|goodbye|see\s+you|see\s+ya|take\s+care|talk\s+later|good\s+night)[\s!.,?]*$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^(thanks|thank\s+you|thank\s+you\s+so\s+much|ok|okay|alright|got\s+it|yes|no|nope|yeah)[\s!.,?]*$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^(who\s+are\s+you|what\s+are\s+you|are\s+you\s+a\s+bot|what\s+can\s+you\s+do|help)[\s!.,?]*$",
        re.IGNORECASE,
    ),
]

_EMOTION_KEYWORDS: dict[str, tuple[str, ...]] = {
    "anxiety": ("anxious", "anxiety", "panic", "panicking", "nervous", "worried", "worry", "overthinking", "uneasy", "dread", "racing thoughts"),
    "stress": ("stressed", "stress", "overwhelmed", "burnout", "pressure", "deadline", "exhausted", "drained", "too much"),
    "sadness": ("sad", "depressed", "depression", "lonely", "isolated", "hopeless", "worthless", "cry", "crying", "grieving", "heartbroken", "empty", "down", "miserable"),
    "anger": ("angry", "mad", "furious", "frustrated", "irritated", "annoyed", "resentful", "rage"),
    "sleep": ("insomnia", "sleepless", "can't sleep", "cannot sleep", "trouble sleeping", "nightmare", "awake all night", "restless"),
    "gratitude": ("grateful", "thankful", "blessed", "appreciate", "appreciative"),
    "happiness": ("happy", "joyful", "excited", "great", "wonderful", "fantastic", "amazing", "thriving", "proud", "motivated", "optimistic"),
    "calm": ("calm", "peaceful", "relaxed", "serene", "relieved", "refreshed", "content"),
    "mindfulness": ("mindful", "present", "balanced", "steady", "grounded", "ordinary", "routine", "normal", "so-so"),
}

_INTENT_SIGNAL: dict[str, tuple[str, float, str]] = {
    "mood_great": ("positive", 0.55, "happiness"),
    "mood_neutral": ("neutral", 0.0, "mindfulness"),
    "mood_sad": ("negative", -0.55, "sadness"),
    "mood_anxious": ("negative", -0.55, "anxiety"),
    "mood_stressed": ("negative", -0.50, "stress"),
    "mood_angry": ("negative", -0.50, "anger"),
    "sleep_issues": ("negative", -0.45, "sleep"),
    "crisis_self_harm": ("negative", -0.95, "crisis"),
}

_NON_RECOMMEND_INTENTS = {"greet", "goodbye", "affirm", "deny", "bot_challenge", "thank_you"}


def detect_crisis(text: str) -> bool:
    """Return True if the message contains self-harm or suicidal ideation markers."""
    cleaned = (text or "").strip()
    if not cleaned:
        return False
    return any(pattern.search(cleaned) for pattern in _CRISIS_PATTERNS)


def _is_trivial_conversational(text: str) -> bool:
    cleaned = (text or "").strip()
    if not cleaned:
        return True
    return any(pattern.match(cleaned) for pattern in _GREETING_ONLY_PATTERNS)


def _infer_emotion(text: str, sentiment: str, intent_name: str | None = None) -> str:
    lowered = text.lower()
    if detect_crisis(lowered) or intent_name == "crisis_self_harm":
        return "crisis"

    for emotion, keywords in _EMOTION_KEYWORDS.items():
        if any(re.search(rf"\b{re.escape(kw)}\b", lowered) for kw in keywords):
            if sentiment == "negative" and emotion in {"gratitude", "happiness", "calm"}:
                continue
            if sentiment == "positive" and emotion in {"anxiety", "stress", "sadness", "anger", "sleep"}:
                continue
            return emotion

    if intent_name in _INTENT_SIGNAL:
        intent_sentiment, _, intent_emotion = _INTENT_SIGNAL[intent_name]
        if intent_sentiment == sentiment:
            return intent_emotion

    if sentiment == "positive":
        return "happiness"
    if sentiment == "negative":
        return "sadness"
    return "mindfulness"


def analyze_message(
    text: str,
    intent_name: str | None = None,
    intent_confidence: float = 0.0,
) -> dict[str, Any]:
    """Analyze a user message for sentiment (positive/negative/neutral), score, emotion, and crisis risk."""
    cleaned = (text or "").strip()
    if detect_crisis(cleaned) or (intent_name == "crisis_self_harm" and intent_confidence >= 0.55):
        return {
            "sentiment": "negative",
            "score": -0.95,
            "confidence": 0.99,
            "emotion": "crisis",
            "is_crisis": True,
            "should_recommend_videos": True,
        }

    is_video_request = intent_name == "request_video" or any(
        kw in cleaned.lower()
        for kw in ("recommend a video", "suggest a video", "video link", "watch something", "helpful video")
    )

    if _is_trivial_conversational(cleaned) or (
        intent_name in _NON_RECOMMEND_INTENTS
        and intent_confidence >= 0.70
        and len(cleaned.split()) <= 5
        and not is_video_request
    ):
        return {
            "sentiment": "neutral",
            "score": 0.0,
            "confidence": round(max(0.75, intent_confidence), 3),
            "emotion": "neutral",
            "is_crisis": False,
            "should_recommend_videos": False,
        }

    vader_scores = _ANALYZER.polarity_scores(cleaned)
    compound = float(vader_scores["compound"])

    fused_score = compound
    if intent_name in _INTENT_SIGNAL and intent_confidence >= 0.65:
        intent_sentiment, intent_prior, _ = _INTENT_SIGNAL[intent_name]
        # Avoid overriding a clear opposite VADER polarity (e.g., negation like "not happy at all").
        if intent_sentiment == "neutral" and -0.25 < compound < 0.35:
            fused_score = 0.35 * compound
        elif (
            (intent_sentiment == "negative" and compound <= 0.10)
            or (intent_sentiment == "positive" and compound >= -0.10)
        ):
            fused_score = 0.65 * compound + 0.35 * intent_prior

    fused_score = max(-1.0, min(1.0, round(fused_score, 4)))

    if fused_score >= 0.15:
        sentiment = "positive"
    elif fused_score <= -0.15:
        sentiment = "negative"
    else:
        sentiment = "neutral"

    confidence = min(0.99, round(max(0.52, abs(fused_score) * 0.75 + 0.35), 3))
    emotion = _infer_emotion(cleaned, sentiment, intent_name=intent_name)

    return {
        "sentiment": sentiment,
        "score": fused_score,
        "confidence": confidence,
        "emotion": emotion,
        "is_crisis": False,
        "should_recommend_videos": True,
    }


def analyze_communication_pattern(history: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize sentiment distribution, trajectory trend, and streak across conversation history."""
    if not history:
        return {
            "total_messages": 0,
            "positive_count": 0,
            "neutral_count": 0,
            "negative_count": 0,
            "positive_pct": 0.0,
            "neutral_pct": 0.0,
            "negative_pct": 0.0,
            "average_score": 0.0,
            "dominant_sentiment": "neutral",
            "trend": "initial",
            "consecutive_negative": 0,
        }

    total = len(history)
    pos = sum(1 for item in history if item.get("sentiment") == "positive")
    neu = sum(1 for item in history if item.get("sentiment") == "neutral")
    neg = sum(1 for item in history if item.get("sentiment") == "negative")

    scores = [float(item.get("score", 0.0) or 0.0) for item in history]
    avg_score = round(sum(scores) / total, 4)

    counts = {"positive": pos, "neutral": neu, "negative": neg}
    dominant = max(("negative", "positive", "neutral"), key=lambda key: (counts[key], key == "neutral"))

    consecutive_negative = 0
    for item in reversed(history):
        if item.get("sentiment") == "negative":
            consecutive_negative += 1
        else:
            break

    if total < 2:
        trend = "initial"
    else:
        midpoint = max(1, total // 2)
        earlier_avg = sum(scores[:midpoint]) / len(scores[:midpoint])
        recent_avg = sum(scores[midpoint:]) / len(scores[midpoint:])
        delta = recent_avg - earlier_avg
        if delta >= 0.18:
            trend = "improving"
        elif delta <= -0.18:
            trend = "declining"
        else:
            trend = "stable"

    return {
        "total_messages": total,
        "positive_count": pos,
        "neutral_count": neu,
        "negative_count": neg,
        "positive_pct": round((pos / total) * 100, 1),
        "neutral_pct": round((neu / total) * 100, 1),
        "negative_pct": round((neg / total) * 100, 1),
        "average_score": avg_score,
        "dominant_sentiment": dominant,
        "trend": trend,
        "consecutive_negative": consecutive_negative,
    }


def _pick_variant(seed_text: str, options: list[str]) -> str:
    digest = hashlib.sha256(seed_text.encode("utf-8")).digest()
    return options[digest[0] % len(options)]


def generate_therapist_reply(
    text: str,
    analysis: dict[str, Any],
    pattern: dict[str, Any] | None = None,
    intent_name: str | None = None,
) -> str:
    """Generate a supportive, therapist-inspired response tailored to sentiment, emotion, and pattern."""
    sentiment = analysis.get("sentiment", "neutral")
    emotion = analysis.get("emotion", "neutral")
    is_crisis = bool(analysis.get("is_crisis"))
    consecutive_neg = int((pattern or {}).get("consecutive_negative", 0))
    trend = (pattern or {}).get("trend", "initial")

    if is_crisis:
        return (
            "I hear how much pain you are carrying right now, and I want you to be safe. "
            "You do not have to go through this alone — please reach out right now to someone who can support you in real time:\n"
            "• US & Canada: Call or text 988 (Suicide & Crisis Lifeline, free and 24/7)\n"
            "• Crisis Text Line: Text HOME to 741741\n"
            "• International helplines: https://findahelpline.com\n"
            "If you are in immediate danger, please call your local emergency number or go to the nearest emergency room. "
            "If you feel able, take one slow breath with me right now and let me know if there is a trusted person nearby you can contact."
        )

    if intent_name == "greet" and not analysis.get("should_recommend_videos"):
        return (
            "Hello, I'm glad you checked in today. This is a calm, judgment-free space — "
            "how are you feeling right now, and what has been on your mind?"
        )

    if intent_name == "goodbye" and not analysis.get("should_recommend_videos"):
        return (
            "Thank you for taking time to check in with yourself today. "
            "Be gentle with yourself, and come back anytime you want to talk."
        )

    if intent_name == "thank_you" and not analysis.get("should_recommend_videos"):
        return (
            "You are very welcome. Checking in with your emotions takes real care — "
            "I'm right here whenever you'd like to continue reflecting."
        )

    if intent_name == "bot_challenge" and not analysis.get("should_recommend_videos"):
        return (
            "I'm your Mental Health Support Chatbot powered by Rasa NLU and sentiment analysis. "
            "I listen to how you're feeling, reflect supportive coping steps, and recommend helpful videos tailored to your mood."
        )

    if sentiment == "negative":
        openers = {
            "anxiety": [
                "It sounds like your mind is carrying a lot of worry right now, and feeling anxious can be exhausting.",
                "Anxiety can make everything feel urgent at once. Thank you for naming what you're feeling.",
            ],
            "stress": [
                "That sounds like a heavy load to carry, and it makes complete sense that you're feeling stressed.",
                "When demands pile up, feeling overwhelmed is a natural signal that you need breathing room.",
            ],
            "sadness": [
                "I'm really sorry things feel heavy right now. Feeling down or lonely takes a quiet toll.",
                "Thank you for trusting me with how you're feeling — carrying sadness on your own is hard.",
            ],
            "anger": [
                "It sounds like you're feeling deeply frustrated right now, and your feelings are valid.",
                "That kind of irritation or anger often shows up when something important feels out of balance.",
            ],
            "sleep": [
                "Not getting restful sleep wears down both your body and your emotional resilience.",
                "Lying awake with a busy mind can feel frustrating and isolating.",
            ],
        }
        techniques = {
            "anxiety": "Try a 4-4-4-4 box breath right now (inhale 4s, hold 4s, exhale 4s, hold 4s) or name 3 things you can physically feel around you.",
            "stress": "Let's shrink the moment down: what is just one small task you can set aside or postpone for the next hour?",
            "sadness": "Offer yourself the same kindness you'd give a close friend — even one small comforting step counts today.",
            "anger": "Unclench your jaw, drop your shoulders, and take two slow exhales longer than your inhales to let the physical tension settle.",
            "sleep": "Dimming screens and taking five slow belly breaths can help signal safety and rest to your nervous system.",
        }
        opener = _pick_variant(text, openers.get(emotion, openers["sadness"]))
        technique = techniques.get(emotion, techniques["anxiety"])
        pattern_note = ""
        if consecutive_neg >= 3:
            pattern_note = (
                " I've also noticed several heavy check-ins in a row — if this distress keeps persisting, "
                "talking with a licensed counselor or trusted person in your life could give you deeper support."
            )
        return (
            f"{opener} {technique}{pattern_note} "
            "I've shared a couple of calming, evidence-based videos below tailored to what you're going through. "
            "Would you like to share a little more about what triggered this feeling?"
        )

    if sentiment == "positive":
        positive_openers = [
            "It's wonderful to hear you're feeling good right now! Moments of genuine lift are worth noticing and savoring.",
            "I'm really glad things are feeling bright for you today. Recognizing what brings you energy builds lasting resilience.",
            "That sounds genuinely uplifting! Taking a beat to appreciate positive moments helps reinforce them.",
        ]
        opener = _pick_variant(text, positive_openers)
        trend_note = (
            " It's encouraging to see your emotional tone lifting across our conversation too."
            if trend == "improving"
            else ""
        )
        return (
            f"{opener}{trend_note} "
            "What has contributed most to this good feeling today? "
            "I've also picked a couple of inspiring videos below to keep that positive momentum going."
        )

    neutral_openers = [
        "Thank you for checking in. Even steady, ordinary days are a helpful time to pause and notice how your mind and body feel.",
        "It sounds like today has been fairly balanced or routine. Checking in during calm moments helps build emotional awareness.",
        "I appreciate you sharing where things stand right now — a neutral headspace can be a great anchor for mindful reflection.",
    ]
    opener = _pick_variant(text, neutral_openers)
    return (
        f"{opener} "
        "Is there anything subtle lingering in the background, or a small intention you'd like to set for the rest of your day? "
        "Below are a few short mindfulness videos if you'd like a gentle mental reset."
    )
