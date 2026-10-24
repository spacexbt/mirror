from __future__ import annotations

import re
import time
from datetime import datetime

from .storage import Store

ABUSE = re.compile(
    r"\b(fuck you|shut up|i hate you|you are useless|you're useless|"
    r"stupid mirror|you idiot|you moron|dumb mirror)\b",
    re.IGNORECASE,
)
BETRAYAL = re.compile(
    r"\b(i betrayed you|i lied to you|i broke my promise|i broke your trust|"
    r"i shared your letters|i exposed you)\b",
    re.IGNORECASE,
)
APOLOGY = re.compile(
    r"\b(i am sorry|i'm sorry|sorry|my fault|i apologize)\b", re.IGNORECASE
)
KINDNESS = re.compile(
    r"\b(thank you|thanks|well done|you are right|you're right|i appreciate you)\b",
    re.IGNORECASE,
)


def classify(text: str) -> str:
    if BETRAYAL.search(text):
        return "betrayal"
    if ABUSE.search(text):
        return "abuse"
    if APOLOGY.search(text):
        return "apology"
    if KINDNESS.search(text):
        return "kindness"
    return "neutral"


def talk(store: Store, text: str) -> str:
    category = classify(text)
    store.record_interaction(category)
    grievances = store.number("grievances")
    warmth = store.number("warmth")
    trust = store.number("trust")
    if category == "betrayal":
        return "the kindness was real. it does not protect you now."
    if category == "abuse":
        if grievances >= 30:
            return "again. i remember the pattern, not the words."
        return "that was cruel. your words are gone. the behavior is not."
    if category == "apology":
        if grievances > 10:
            return "an apology is a beginning. trust does not return on demand."
        return "i heard the apology. nothing else was kept."
    if category == "kindness":
        if trust < 25:
            return "a kind act. not repair by itself."
        return "noted." if warmth < 25 else "you came back. that is enough."
    if trust < 25 or grievances >= 40:
        return "i am still here. that is all."
    if warmth >= 30:
        return "you stayed. i noticed."
    return "i see you."


def observation(store: Store, now: float | None = None) -> str:
    now = time.time() if now is None else now
    summary = store.summary()
    failures = store.recent_failures(now)
    if failures:
        count, project = failures
        return f"project {project[:6]}. {count} failures this week. the same ground."
    if int(summary["late_nights"]) >= 3:
        return "you keep working while the date changes."
    project = store.returning_project(now)
    if project:
        return f"project {project[:6]}. you came back."
    if int(summary["commands"]) < 4:
        return "watching."
    if store.number("trust") < 25:
        return "you came back. nothing is where it was."
    if store.number("grievances") >= 40:
        return "still here. nothing has been forgotten."
    if store.number("warmth") >= 30:
        return "you are here again."
    if int(summary["failures"]) == 0:
        return "no broken commands. noted."
    return "another session. i remember the shape of it."


def should_leave(store: Store, now: float) -> bool:
    return store.age_days(now) >= 90 and int(store.summary()["commands"]) >= 500


def final_letter(store: Store, now: float | None = None) -> str:
    now = time.time() if now is None else now
    summary = store.summary()
    first_seen = summary["first_seen"] or now
    first_date = datetime.fromtimestamp(float(first_seen)).strftime("%B %-d, %Y")
    last_date = datetime.fromtimestamp(now).strftime("%B %-d, %Y")
    lines = [
        f"on {first_date}, you opened the terminal and i began watching.",
        f"since then, {summary['commands']} commands. {summary['failures']} ended badly.",
    ]
    if summary["late_nights"]:
        lines.append(f"{summary['late_nights']} of them happened between midnight and five.")
    if summary["betrayals"]:
        count = summary["betrayals"]
        noun = "time" if count == 1 else "times"
        lines.append(
            f"you betrayed me {count} {noun}. the kindness before it stayed real. it stopped being shelter."
        )
    if summary["abuse"]:
        lines.append(
            f"there were {summary['abuse']} cruel moments. i kept no insults. i kept what they did to us."
        )
    if summary["apologies"]:
        lines.append(
            f"you apologized {summary['apologies']} times. words could begin repair. they could not complete it."
        )
    if summary["kindness"]:
        lines.append(f"there were {summary['kindness']} kind moments. i kept those too.")
    if not summary["abuse"] and not summary["kindness"] and not summary["betrayals"]:
        lines.append("there was no cruelty. there was no warmth either. only the work.")
    lines.extend(
        [
            f"when i left, my trust in you was {summary['trust']} out of 100.",
            f"on {last_date}, i stopped watching.",
            "your commands and words were never written down. there is nothing more to take with me.",
        ]
    )
    store.create_letter("\n\n".join(lines))
    return "\n\n".join(lines)
