# app/routes/pronunciation_recommend_route.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.pronunciation_models import UserPronunciationProfile, PhonemePerformance

router = APIRouter(prefix="/api/v1/pronunciation", tags=["Pronunciation"])

# Expand later
SENTENCE_BANK = {
    "θ": [
        {"sentence": "Think about the thing.", "difficulty": "basic"},
        {"sentence": "Three thousand thoughts.", "difficulty": "intermediate"},
    ],
    "ð": [
        {"sentence": "This is the day that they arrived.", "difficulty": "basic"},
        {"sentence": "Those weathered clothes are theirs.", "difficulty": "intermediate"},
    ],
    "ə": [
        {"sentence": "The problem was about a banana.", "difficulty": "basic"},
        {"sentence": "A collection of unusual animals.", "difficulty": "intermediate"},
    ],
    "f": [
        {"sentence": "Five frogs fled from the fog.", "difficulty": "basic"},
        {"sentence": "The effort to perfect the draft was effective.", "difficulty": "intermediate"},
    ],
    "m": [
        {"sentence": "Make my mother some lemon jam.", "difficulty": "basic"},
        {"sentence": "The minimum amount was met immediately.", "difficulty": "intermediate"},
    ],
    "l": [
        {"sentence": "Lucy likes light blue balloons.", "difficulty": "basic"},
        {"sentence": "The tall fellow left the village slowly.", "difficulty": "intermediate"},
    ],
    "i": [
        {"sentence": "She sees three green trees.", "difficulty": "basic"},
        {"sentence": "He believes the team will achieve the lead.", "difficulty": "intermediate"},
    ],
    "oʊ": [
        {"sentence": "Go home and open the old stove.", "difficulty": "basic"},
        {"sentence": "The cold stone road goes below the slope.", "difficulty": "intermediate"},
    ],
    "d": [
        {"sentence": "Dad did a good deed today.", "difficulty": "basic"},
        {"sentence": "David decided to add the details to the document.", "difficulty": "intermediate"},
    ],
    "z": [
        {"sentence": "Zoe sees zebras at the zoo.", "difficulty": "basic"},
        {"sentence": "The buzzing noise caused a dozen problems.", "difficulty": "intermediate"},
    ],
    "w": [
        {"sentence": "We will walk with the wind.", "difficulty": "basic"},
        {"sentence": "Would you wait while I wash the window?", "difficulty": "intermediate"},
    ],
    "r": [
        {"sentence": "Run around the red river.", "difficulty": "basic"},
        {"sentence": "The rural road required repairs after the rain.", "difficulty": "intermediate"},
    ],
    "n": [
        {"sentence": "Nine new notebooks near the window.", "difficulty": "basic"},
        {"sentence": "Neither of the knives needs cleaning now.", "difficulty": "intermediate"},
    ],
    "dʒ": [
        {"sentence": "Just enjoy the job.", "difficulty": "basic"},
        {"sentence": "The judge rejected the major changes.", "difficulty": "intermediate"},
    ],
    "ɔɪ": [
        {"sentence": "The boy enjoyed the toy.", "difficulty": "basic"},
        {"sentence": "Roy avoided the noisy oil joint.", "difficulty": "intermediate"},
    ],
    "ɪ": [
        {"sentence": "It is a big fish dish.", "difficulty": "basic"},
        {"sentence": "The village is built on a hilly ridge.", "difficulty": "intermediate"},
    ],
    "ŋ": [
        {"sentence": "Sing a long song this evening.", "difficulty": "basic"},
        {"sentence": "The ringing and clanging was getting stronger.", "difficulty": "intermediate"},
    ],
    "s": [
        {"sentence": "Sam sells sea shells by the sea shore.", "difficulty": "basic"},
        {"sentence": "The scientist stressed the success of the system.", "difficulty": "intermediate"},
    ],
    "æ": [
        {"sentence": "The cat sat on the black mat.", "difficulty": "basic"},
        {"sentence": "Ann has a bad habit of clapping hands rapidly.", "difficulty": "intermediate"},
    ],
    "p": [
        {"sentence": "Peter picked a pack of peppers.", "difficulty": "basic"},
        {"sentence": "The puppet performance appeared pretty impressive.", "difficulty": "intermediate"},
    ],
    "b": [
        {"sentence": "Bob bought a big blue bag.", "difficulty": "basic"},
        {"sentence": "The baby grabbed the rubber ball beside the bed.", "difficulty": "intermediate"},
    ],
    "t": [
        {"sentence": "Take the train to town today.", "difficulty": "basic"},
        {"sentence": "The tourist took a taste of the tasty tart.", "difficulty": "intermediate"},
    ],
    "k": [
        {"sentence": "Keep the cat in the kitchen.", "difficulty": "basic"},
        {"sentence": "The colorful kite caught the cool breeze quickly.", "difficulty": "intermediate"},
    ],
    "g": [
        {"sentence": "Get the big green bag.", "difficulty": "basic"},
        {"sentence": "The goat grabbed the green grass near the garden gate.", "difficulty": "intermediate"},
    ],
    "v": [
        {"sentence": "Vivian loves to visit every valley.", "difficulty": "basic"},
        {"sentence": "The driver moved the vehicle over the curved road.", "difficulty": "intermediate"},
    ],
    "h": [
        {"sentence": "He held his hat in his hand.", "difficulty": "basic"},
        {"sentence": "The happy hiker headed home through the hills.", "difficulty": "intermediate"},
    ],
    "j": [
        {"sentence": "Yes you can use your yellow yacht.", "difficulty": "basic"},
        {"sentence": "The young student yearned for years to play.", "difficulty": "intermediate"},
    ],
    "ʃ": [
        {"sentence": "She sells shells at the shore.", "difficulty": "basic"},
        {"sentence": "The sharp shadow showed the shape of the shed.", "difficulty": "intermediate"},
    ],
    "tʃ": [
        {"sentence": "Charles chose to eat peach and cheese.", "difficulty": "basic"},
        {"sentence": "The teacher challenged each child to reach their potential.", "difficulty": "intermediate"},
    ],
    "ʒ": [
        {"sentence": "It was a usual pleasure.", "difficulty": "basic"},
        {"sentence": "The beige garage had a casual and leisurely atmosphere.", "difficulty": "intermediate"},
    ],
    "aɪ": [
        {"sentence": "I like to fly kites at night.", "difficulty": "basic"},
        {"sentence": "The bright light guided my eyes through the wide sky.", "difficulty": "intermediate"},
    ],
    "aʊ": [
        {"sentence": "How now brown cow.", "difficulty": "basic"},
        {"sentence": "The loud crowd gathered around the south mountain town.", "difficulty": "intermediate"},
    ],
    "ʌ": [
        {"sentence": "The sun comes up above the mud.", "difficulty": "basic"},
        {"sentence": "The young monk studied until the summer was done.", "difficulty": "intermediate"},
    ],
    "ʊ": [
        {"sentence": "Look at the good book.", "difficulty": "basic"},
        {"sentence": "The woman stood by the wooden foot of the brook.", "difficulty": "intermediate"},
    ],
    "u": [
        {"sentence": "Move the blue shoe to the room.", "difficulty": "basic"},
        {"sentence": "The smooth music from the flute flew through the school.", "difficulty": "intermediate"},
    ],
    "ɛ": [
        {"sentence": "Get the red pen off the desk.", "difficulty": "basic"},
        {"sentence": "The healthy men meant to measure the length carefully.", "difficulty": "intermediate"},
    ],
    "ɑ": [
        {"sentence": "The father watched the calm dark water.", "difficulty": "basic"},
        {"sentence": "The honest artist carved a large marble heart.", "difficulty": "intermediate"},
    ],
    "ɔ": [
        {"sentence": "The dog walked along the long hall.", "difficulty": "basic"},
        {"sentence": "The author often talked about the awesome autumn fog.", "difficulty": "intermediate"},
    ],
}
Just replace your existing SENTENCE_BANK dict in pronunciation_recommend_route.py with this — no other changes needed. All 18 weak phonemes from your response now have exercises, and it covers every phoneme in your VALID_IPA set so future weak phonemes will also be handled.
}


def safe_level_progress(profile: UserPronunciationProfile):
    """
    Guarantee a valid dict structure for level_progress.
    Avoids KeyError and NoneType crashes.
    """
    lp = profile.level_progress or {}

    return {
        "exercises_at_level": int(lp.get("exercises_at_level", 0)),
        "required": int(lp.get("required_for_next", 20)),
        "current": lp.get("current", profile.current_level),
        "avg_score_at_level": float(lp.get("avg_score_at_level", 0))
    }


def compute_next_milestone(profile: UserPronunciationProfile):
    """
    Determines the next milestone safely.
    """
    lp = safe_level_progress(profile)

    remaining = lp["required"] - lp["exercises_at_level"]

    if remaining <= 0:
        return "You are eligible to level up after scoring above 75% consistently."

    return f"Complete {remaining} more exercises to reach the next level."


@router.get("/recommendations/{user_id}")
def get_pronunciation_recommendations(user_id: int, db: Session = Depends(get_db)):
    """
    Generate a personalized recommendation set based on weak phonemes.
    """

    profile = db.query(UserPronunciationProfile).filter_by(user_id=user_id).first()
    if not profile:
        return {
            "focus_areas": [],
            "suggested_practice_time_mins": 10,
            "next_milestone": "No data available. Complete your first exercise."
        }

    # Fetch phoneme performance
    phonemes = db.query(PhonemePerformance).filter_by(user_id=user_id).all()

    weak_phonemes = []
    for p in phonemes:
        if p.accuracy_pct is not None:
            acc = float(p.accuracy_pct)
            if acc < 50:
                weak_phonemes.append(p)

    focus_areas = []
    for w in weak_phonemes:
        examples = SENTENCE_BANK.get(w.phoneme, [])
        focus_areas.append({
            "phoneme": w.phoneme,
            "exercises": examples
        })

    next_milestone = compute_next_milestone(profile)

    return {
        "focus_areas": focus_areas,
        "suggested_practice_time_mins": 15,
        "next_milestone": next_milestone
    }