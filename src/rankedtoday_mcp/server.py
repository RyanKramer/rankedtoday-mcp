"""Ranked Today MCP Server — League of Legends math and cognitive-readiness reference.

Every tool is a pure function: no API key, no Riot account, no network calls.
Each one shows its arithmetic, because every tool in this category is an
estimate and the ones that hide that fact are the ones to distrust.

Usage:
    rankedtoday-mcp                 # run the server
    python -m rankedtoday_mcp       # alternative

Configuration: none required.

Web versions: https://shouldiplayrankedtoday.com/tools
"""

import logging
from datetime import date, datetime, timezone

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP(
    "RankedToday",
    instructions=(
        "League of Legends math (MMR estimation from LP flow, climb projections, "
        "KDA, hours played) and cognitive-readiness reference data. Use these "
        "when the user asks about their rank, LP gains, how long a climb takes, "
        "or how sleep and fatigue affect gaming performance. Every estimate "
        "shows its arithmetic and its error bars."
    ),
)

SITE = "https://shouldiplayrankedtoday.com"

# Level-to-hours constants. Riot publishes no lifetime counter, so this is the
# only signal that covers a whole account history.
GAMES_TO_30 = 120
XP_PER_LEVEL = 2500
XP_PER_GAME = 200
MINUTES_PER_GAME = 35  # includes queue, champ select and loading, not just match time


@mcp.tool
def estimate_mmr(lp_gain: int, lp_loss: int, current_rank: str = "") -> dict:
    """Estimate where your MMR sits relative to your rank, from LP flow.

    Riot does not expose MMR and no site can read it. What MMR does leak is the
    exchange rate: when MMR matches rank, wins and losses move you roughly
    symmetrically. Asymmetry is the signal.
    """
    if lp_gain <= 0 or lp_loss <= 0:
        return {"error": "lp_gain and lp_loss must both be positive numbers."}
    gap = lp_gain - lp_loss
    # Roughly one division of drift per 5 LP of asymmetry.
    divisions = round(abs(gap) / 5.0, 1)
    if gap > 3:
        verdict = "above"
        meaning = (
            "Your MMR is ABOVE your rank. The system is paying you extra for wins and "
            "forgiving losses to pull you upward. This is the good side to be on: keep queueing."
        )
    elif gap < -3:
        verdict = "below"
        meaning = (
            "Your MMR is BELOW your rank. The system is paying you less for wins and "
            "charging more for losses to drag you back. Only sustained winning fixes it."
        )
    else:
        verdict = "aligned"
        meaning = "Your MMR is roughly ALIGNED with your rank. Gains and losses are near symmetric."
    return {
        "lp_gain": lp_gain,
        "lp_loss": lp_loss,
        "asymmetry": gap,
        "mmr_vs_rank": verdict,
        "estimated_drift_divisions": divisions if verdict != "aligned" else 0,
        "current_rank": current_rank,
        "interpretation": meaning,
        "honesty_note": (
            "This is an inference from the exchange rate, not a reading of the real number. "
            "Riot removed public MMR from the API years ago; any site printing an exact MMR "
            "from a summoner name is guessing without saying so."
        ),
    }


@mcp.tool
def hours_played(account_level: int, minutes_per_game: int = MINUTES_PER_GAME) -> dict:
    """Estimate lifetime hours from account level, with the math shown.

    Levels are earned almost entirely by finishing games, so level is the only
    signal that reflects a whole account history. Expect about 20% error.
    """
    if account_level < 1:
        return {"error": "account_level must be at least 1."}
    if account_level <= 30:
        games = round(GAMES_TO_30 * (account_level / 30.0))
    else:
        games_per_level = XP_PER_LEVEL / XP_PER_GAME
        games = round(GAMES_TO_30 + (account_level - 30) * games_per_level)
    minutes = games * minutes_per_game
    hours = minutes / 60.0
    return {
        "account_level": account_level,
        "estimated_games": games,
        "minutes_per_game": minutes_per_game,
        "estimated_hours": round(hours, 1),
        "estimated_days": round(hours / 24.0, 1),
        "range_low_hours": round(hours * 0.8, 1),
        "range_high_hours": round(hours * 1.2, 1),
        "math": (
            f"Level 30 is about {GAMES_TO_30} games. Each level after costs about "
            f"{XP_PER_LEVEL} XP at roughly {XP_PER_GAME} XP per finished game, so about "
            f"{XP_PER_LEVEL // XP_PER_GAME} games per level. Times {minutes_per_game} "
            "minutes per game including queue, champion select and loading."
        ),
        "what_it_cannot_see": [
            "ARAM and bot games, which pay different XP",
            "XP boosts, which make the estimate read high",
            "Other accounts — your true total is the sum of all of them",
        ],
        "honesty_note": "Plus or minus about 20%. Every 'exact' counter online runs this same arithmetic.",
    }


@mcp.tool
def climb_calculator(
    current_lp_total: int,
    target_lp_total: int,
    winrate_pct: float,
    lp_per_win: int = 25,
    lp_per_loss: int = 25,
) -> dict:
    """How many games a climb takes at a given winrate, or whether it runs backward.

    LP totals are cumulative: one division is 100 LP, one tier is 400 LP. So
    Gold IV 0 LP to Plat IV 0 LP is 400.
    """
    if not 0 < winrate_pct < 100:
        return {"error": "winrate_pct must be between 0 and 100."}
    wr = winrate_pct / 100.0
    net_per_game = wr * lp_per_win - (1 - wr) * lp_per_loss
    breakeven = lp_per_loss / (lp_per_win + lp_per_loss) * 100
    needed = target_lp_total - current_lp_total

    if net_per_game <= 0:
        return {
            "net_lp_per_game": round(net_per_game, 2),
            "breakeven_winrate_pct": round(breakeven, 1),
            "games_required": None,
            "verdict": (
                f"At {winrate_pct}% you are at or below your breakeven winrate of "
                f"{breakeven:.1f}%. More games means LESS LP — the climb runs backward. "
                "The cheapest winrate you will ever buy is not queueing on your bad days."
            ),
        }
    games = needed / net_per_game
    return {
        "lp_needed": needed,
        "net_lp_per_game": round(net_per_game, 2),
        "breakeven_winrate_pct": round(breakeven, 1),
        "games_required": round(games),
        "estimated_hours": round(games * MINUTES_PER_GAME / 60.0, 1),
        "math": (
            f"Net LP per game = {winrate_pct}% x {lp_per_win} - {100 - winrate_pct}% x "
            f"{lp_per_loss} = {net_per_game:.2f}. {needed} LP / {net_per_game:.2f} = "
            f"{round(games)} games."
        ),
        "note": (
            "The math is brutally sensitive to small winrate changes: a few points "
            "roughly halves or doubles the games required."
        ),
    }


@mcp.tool
def kda(kills: int, deaths: int, assists: int, role: str = "") -> dict:
    """Calculate KDA with an honest, role-aware read."""
    if deaths == 0:
        ratio = None
        display = "Perfect KDA"
    else:
        ratio = round((kills + assists) / deaths, 2)
        display = str(ratio)
    if ratio is None:
        band = "No deaths — the ratio is undefined rather than infinite."
    elif ratio >= 3.0:
        band = "Strong."
    elif ratio >= 2.0:
        band = "Solid."
    else:
        band = "Below the typical solid range."
    role_note = ""
    r = role.strip().lower()
    if r in {"support", "sup", "jungle", "jg", "jungler"}:
        role_note = "Supports and junglers run higher through assists; 3-4+ is normal for a good support."
    elif r in {"top", "mid", "adc", "bot"}:
        role_note = "Solo laners and carries take more deaths for their kills; judge against your role."
    return {
        "kda": display,
        "ratio": ratio,
        "kills": kills, "deaths": deaths, "assists": assists,
        "formula": "(kills + assists) / deaths",
        "read": band,
        "role_note": role_note,
        "caveat": (
            "When KDA and winrate disagree, believe the winrate. A high KDA at a losing "
            "winrate usually describes safe stat-farming while the map slips."
        ),
    }


@mcp.tool
def readiness_reference() -> dict:
    """What the research actually supports about cognition and gaming performance.

    Included because these numbers get misquoted constantly in both directions.
    """
    return {
        "supported": [
            {
                "finding": "One night of sleep deprivation slows simple reaction time by roughly +49 ms",
                "context": "Lab-measured, psychomotor vigilance task.",
            },
            {
                "finding": "Sleep deprivation produces about 5x more attention lapses",
                "context": "Same paradigm. Lapses matter more than average speed for gameplay.",
            },
            {
                "finding": "In a 516-player study of League players, reaction speed was the strongest cognitive correlate of rank on record",
                "context": "A correlation ACROSS players. It does not establish that getting faster makes you climb.",
            },
            {
                "finding": "Most people can track about 4 moving targets among identical distractors",
                "context": "Multiple object tracking. The limit is attentional, not visual.",
            },
            {
                "finding": "Adding a two-way choice to a reaction task costs roughly 50-150 ms",
                "context": "Hick's law. Real gameplay is choice reaction, not simple reaction.",
            },
        ],
        "not_supported": [
            "That a cognitive score predicts whether you will win a given game.",
            "That brain-training transfers broadly to untrained tasks — far-transfer evidence is weak.",
            "That reaction-time supplements meaningfully raise your ceiling.",
        ],
        "the_honest_framing": (
            "Readiness is a probabilistic personal signal, not a win predictor. A controlled "
            "study found sleep-deprived players' cognition tanked while game outcomes did not "
            "move much. What is reliably true is that your own distance from your own ceiling "
            "varies day to day, and that gap is the recoverable part."
        ),
        "free_tests": f"{SITE}/tests",
    }


@mcp.tool
def hardware_latency_budget(
    refresh_hz: int = 60,
    mouse_polling_hz: int = 125,
    is_touchscreen: bool = False,
) -> dict:
    """Estimate how much of a reaction-test score is equipment rather than you.

    A reaction test measures the whole chain: the screen has to draw the
    stimulus and the input device has to report the response. Only the middle
    is you, and the rest is worth real milliseconds.
    """
    frame_ms = 1000.0 / max(refresh_hz, 1)
    display_avg = frame_ms / 2.0
    polling_ms = 1000.0 / max(mouse_polling_hz, 1)
    touch = 25.0 if is_touchscreen else 0.0
    total = display_avg + polling_ms / 2.0 + touch
    return {
        "display_refresh_hz": refresh_hz,
        "frame_interval_ms": round(frame_ms, 2),
        "display_added_ms_avg": round(display_avg, 2),
        "display_added_ms_worst": round(frame_ms, 2),
        "input_added_ms_avg": round(polling_ms / 2.0, 2),
        "touchscreen_penalty_ms": touch,
        "estimated_total_added_ms": round(total, 1),
        "explanation": (
            f"A {refresh_hz} Hz display draws a new frame every {frame_ms:.1f} ms, so on "
            f"average the stimulus waits about {display_avg:.1f} ms before it physically exists."
        ),
        "why_it_matters": (
            "This delay is a constant for a given setup, so it cancels out entirely when you "
            "compare your score against your own history on the same machine, and never "
            "cancels out when you compare against a stranger. That is the whole argument for "
            "baselines over leaderboards."
        ),
    }


@mcp.tool
def season_countdown(target_date: str, from_date: str = "") -> dict:
    """Days remaining until a ranked season boundary or any other date.

    Pass from_date (YYYY-MM-DD) to compute from a fixed day; otherwise uses today.
    """
    try:
        target = date.fromisoformat(target_date.strip())
    except ValueError:
        return {"error": "target_date must be ISO format (YYYY-MM-DD)."}
    start = date.fromisoformat(from_date.strip()) if from_date.strip() else datetime.now(timezone.utc).date()
    delta = (target - start).days
    return {
        "from": start.isoformat(),
        "target": target_date,
        "days_remaining": delta,
        "weeks_remaining": round(delta / 7.0, 1),
        "passed": delta < 0,
        "note": (
            "Rewards lock at your standing when the boundary hits; climbing after does nothing "
            "for the season that closed. Decay only threatens Diamond and above. The in-client "
            "countdown is the authoritative clock — verify dates there."
        ),
    }


@mcp.tool
def rankedtoday_tools() -> dict:
    """Free tools and cognitive tests on the web."""
    return {
        "free_cognitive_tests": f"{SITE}/tests",
        "tests": [
            "reaction-time", "reflex-test", "visual-memory", "hand-eye-coordination",
            "focus", "attention-span", "multitasking", "sequence-memory", "tracking",
        ],
        "league_tools": f"{SITE}/tools",
        "daily_check": f"{SITE}/register",
        "note": "The cognitive tests are playable with no account and runs are not recorded.",
    }


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
