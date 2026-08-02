<!-- mcp-name: io.github.RyanKramer/rankedtoday-mcp -->

# Ranked Today MCP

League of Legends math and cognitive-readiness reference for AI agents.
Estimate MMR from LP flow, project a climb, calculate KDA and lifetime hours,
and get the research on sleep and reaction time without the folklore.

**No API key. No Riot account. No network calls.** Every tool is a pure
function and every estimate shows its arithmetic.

Web versions: [shouldiplayrankedtoday.com/tools](https://shouldiplayrankedtoday.com/tools)

## Install

```json
{
  "mcpServers": {
    "rankedtoday": {
      "command": "uvx",
      "args": ["rankedtoday-mcp"]
    }
  }
}
```

Or `pip install rankedtoday-mcp`.

## Tools

| Tool | What it does |
|---|---|
| `estimate_mmr` | Infers whether MMR sits above or below your rank from LP gain/loss asymmetry |
| `climb_calculator` | Games required to reach a target LP total, or whether the climb runs backward |
| `kda` | KDA with a role-aware read and the winrate caveat |
| `hours_played` | Lifetime hours from account level, with the math and the error bars |
| `hardware_latency_budget` | How much of a reaction-test score is your monitor and mouse, not you |
| `readiness_reference` | What the sleep/cognition research supports — and explicitly what it does not |
| `season_countdown` | Days to a ranked season boundary |
| `rankedtoday_tools` | Free cognitive tests and League tools on the web |

## Design notes

**Nothing here pretends to read hidden data.** Riot removed public MMR from the
API years ago, and there is no lifetime hours counter. `estimate_mmr` infers
from the LP exchange rate and says so; `hours_played` converts account level and
reports plus-or-minus 20% along with what it cannot see. Any tool printing an
exact MMR from a summoner name is guessing without telling you.

**`readiness_reference` includes the disconfirming evidence.** It lists what the
research supports (+49 ms after one all-nighter, 5x more attention lapses, the
516-player rank correlation) *and* what it does not — including a controlled
study where sleep-deprived players' cognition tanked while game outcomes barely
moved. Readiness is a probabilistic personal signal, never a win predictor.

**`climb_calculator` will tell you the climb runs backward.** Below your
breakeven winrate, more games means less LP. It returns that verdict rather than
a games-required number, because the honest answer is that this climb does not
finish.

## Development

```bash
git clone https://github.com/RyanKramer/rankedtoday-mcp
cd rankedtoday-mcp
pip install -e .
rankedtoday-mcp
```

## About

Built by [Ranked Today](https://shouldiplayrankedtoday.com) — a 3-minute daily
cognitive readiness check for League players. Free
[cognitive tests](https://shouldiplayrankedtoday.com/tests), no signup.

Not affiliated with or endorsed by Riot Games.

MIT licensed.
