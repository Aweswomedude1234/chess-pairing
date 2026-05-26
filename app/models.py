"""
models.py — Data models and Swiss pairing engine for ChessPair.
All pairing logic, tiebreak computation, and tournament state live here.
"""
from __future__ import annotations
import uuid
import json
from dataclasses import dataclass, field
from typing import Optional
from copy import deepcopy


# ─── Player ──────────────────────────────────────────────────────────────────

@dataclass
class Player:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    uscf_id: str = ""
    rating: int = 1200
    section_id: str = ""
    score: float = 0.0
    opponents: list[str] = field(default_factory=list)   # list of player IDs
    colors: list[str] = field(default_factory=list)       # "W" or "B" per round
    results: list[str] = field(default_factory=list)      # "W", "D", "L" per round
    cumulative_scores: list[float] = field(default_factory=list)
    has_received_bye: bool = False
    withdrawn: bool = False
    tiebreaks: dict = field(default_factory=dict)

    def color_balance(self) -> int:
        """Positive = more whites, negative = more blacks."""
        return self.colors.count("W") - self.colors.count("B")

    def would_triple(self, new_color: str) -> bool:
        """Would assigning new_color create three consecutive same-color games?"""
        if len(self.colors) < 2:
            return False
        return self.colors[-1] == new_color and self.colors[-2] == new_color

    def to_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name, "uscf_id": self.uscf_id,
            "rating": self.rating, "section_id": self.section_id,
            "score": self.score, "opponents": self.opponents,
            "colors": self.colors, "results": self.results,
            "cumulative_scores": self.cumulative_scores,
            "has_received_bye": self.has_received_bye, "withdrawn": self.withdrawn,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Player":
        return cls(**{k: v for k, v in d.items() if k != "tiebreaks"})


# ─── Section ─────────────────────────────────────────────────────────────────

@dataclass
class Section:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = "Open"
    max_rating: Optional[int] = None   # None = no ceiling
    min_rating: Optional[int] = None   # None = no floor

    def eligible(self, rating: int) -> bool:
        if self.max_rating is not None and rating > self.max_rating:
            return False
        if self.min_rating is not None and rating < self.min_rating:
            return False
        return True

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name,
                "max_rating": self.max_rating, "min_rating": self.min_rating}

    @classmethod
    def from_dict(cls, d: dict) -> "Section":
        return cls(**d)


# ─── Pairing ─────────────────────────────────────────────────────────────────

@dataclass
class Pairing:
    white_id: str
    black_id: str
    result: Optional[str] = None   # "1-0", "0-1", "1/2-1/2", None=pending


@dataclass
class Round:
    number: int
    pairings: list[Pairing] = field(default_factory=list)
    byes: dict[str, str] = field(default_factory=dict)  # section_id -> player_id


# ─── Tournament ──────────────────────────────────────────────────────────────

@dataclass
class Tournament:
    name: str = "My Tournament"
    location: str = ""
    date: str = ""
    num_rounds: int = 5
    time_control: str = "G/90;d5"
    current_round: int = 0
    status: str = "setup"   # setup | active | complete

    def to_dict(self) -> dict:
        return {
            "name": self.name, "location": self.location, "date": self.date,
            "num_rounds": self.num_rounds, "time_control": self.time_control,
            "current_round": self.current_round, "status": self.status,
        }


# ─── Color Assignment ────────────────────────────────────────────────────────

def assign_colors(p1: Player, p2: Player) -> tuple[str, str]:
    """Return (p1_color, p2_color). Minimize imbalance, avoid triples."""
    b1 = p1.color_balance()
    b2 = p2.color_balance()
    if b1 < b2:
        return "W", "B"
    elif b2 < b1:
        return "B", "W"
    elif p1.would_triple("W"):
        return "B", "W"
    elif p1.would_triple("B"):
        return "W", "B"
    else:
        return "W", "B"  # default white to p1


# ─── Pair Validity ───────────────────────────────────────────────────────────

def valid_pair(p1: Player, p2: Player) -> bool:
    return p2.id not in p1.opponents and p1.id not in p2.opponents


# ─── Backtracking Pairing Solver ─────────────────────────────────────────────

def pair_group_backtrack(players: list[Player]) -> Optional[list[tuple[Player, Player]]]:
    """
    Recursively pair a list of players.
    Returns list of (p1, p2) tuples, or None if no valid pairing found.
    """
    if not players:
        return []
    if len(players) % 2 != 0:
        return None  # caller must handle odd groups

    p1 = players[0]
    for i in range(1, len(players)):
        p2 = players[i]
        if valid_pair(p1, p2):
            remaining = [p for j, p in enumerate(players) if j != 0 and j != i]
            result = pair_group_backtrack(remaining)
            if result is not None:
                return [(p1, p2)] + result
    return None


# ─── Round 1 Pairing ─────────────────────────────────────────────────────────

def generate_round1(players: list[Player]) -> tuple[list[Pairing], Optional[str]]:
    """USCF Round 1: sort by rating, split top/bottom, pair across halves."""
    active = [p for p in players if not p.withdrawn]
    active.sort(key=lambda p: -p.rating)

    bye_player_id = None
    if len(active) % 2 != 0:
        bye_player_id = active[-1].id
        active = active[:-1]

    mid = len(active) // 2
    top = active[:mid]
    bottom = active[mid:]

    pairings = []
    for p1, p2 in zip(top, bottom):
        c1, c2 = assign_colors(p1, p2)
        white = p1 if c1 == "W" else p2
        black = p2 if c1 == "W" else p1
        pairings.append(Pairing(white_id=white.id, black_id=black.id))

    return pairings, bye_player_id


# ─── Swiss Round N Pairing ────────────────────────────────────────────────────

def generate_swiss_round(players: list[Player]) -> tuple[list[Pairing], Optional[str]]:
    """USCF Swiss pairing for rounds 2+. Groups by score, uses backtracking."""
    active = [p for p in players if not p.withdrawn]
    active.sort(key=lambda p: (-p.score, -p.rating))

    # Build score groups
    score_map: dict[float, list[Player]] = {}
    for p in active:
        score_map.setdefault(p.score, []).append(p)

    scores_desc = sorted(score_map.keys(), reverse=True)
    all_pairings: list[Pairing] = []
    floaters: list[Player] = []
    bye_player_id: Optional[str] = None

    for score in scores_desc:
        group = score_map[score] + floaters
        floaters = []

        # Sort within group by rating descending
        group.sort(key=lambda p: -p.rating)

        if len(group) % 2 != 0:
            # Float the lowest-rated player down to next score group
            floaters.append(group[-1])
            group = group[:-1]

        if not group:
            continue

        pairs = pair_group_backtrack(group)
        if pairs is None:
            # Fallback: greedy with relaxed constraints
            pairs = _greedy_fallback(group)

        for p1, p2 in pairs:
            c1, _ = assign_colors(p1, p2)
            white = p1 if c1 == "W" else p2
            black = p2 if c1 == "W" else p1
            all_pairings.append(Pairing(white_id=white.id, black_id=black.id))

    # Handle remaining floaters / odd total
    if floaters:
        bye_eligible = [p for p in floaters if not p.has_received_bye]
        bye_player_id = (bye_eligible[-1] if bye_eligible else floaters[-1]).id

    elif len(active) % 2 != 0:
        # Give bye to lowest score, lowest rating, no previous bye
        candidates = sorted(active, key=lambda p: (p.score, p.rating))
        bye_eligible = [p for p in candidates if not p.has_received_bye]
        bye_player_id = (bye_eligible[0] if bye_eligible else candidates[0]).id

    return all_pairings, bye_player_id


def _greedy_fallback(players: list[Player]) -> list[tuple[Player, Player]]:
    """Greedy pairing ignoring color constraints when backtracking fails."""
    remaining = list(players)
    pairs = []
    while len(remaining) >= 2:
        p1 = remaining.pop(0)
        paired = False
        for i, p2 in enumerate(remaining):
            if valid_pair(p1, p2):
                pairs.append((p1, p2))
                remaining.pop(i)
                paired = True
                break
        if not paired and remaining:
            # Force pair even if repeat (last resort)
            pairs.append((p1, remaining.pop(0)))
    return pairs


# ─── Tiebreak Computation ────────────────────────────────────────────────────

def compute_tiebreaks(players: list[Player]) -> None:
    """Compute all USCF tiebreaks in-place using final scores."""
    by_id = {p.id: p for p in players}

    for p in players:
        opp_scores = sorted([by_id[oid].score for oid in p.opponents if oid in by_id])

        # Modified Median: remove highest if score ≤ 50%, lowest if > 50%
        mod_median = 0.0
        if opp_scores:
            total_possible = len(p.results)
            pct = p.score / total_possible if total_possible else 0
            trimmed = opp_scores[:-1] if pct > 0.5 else opp_scores[1:]
            mod_median = sum(trimmed) if trimmed else sum(opp_scores)

        # Solkoff: sum of all opponent scores
        solkoff = sum(opp_scores)

        # Cumulative: sum of running scores after each round
        cumulative = sum(p.cumulative_scores)

        # Opposition Cumulative
        opp_cumulative = sum(
            sum(by_id[oid].cumulative_scores)
            for oid in p.opponents if oid in by_id
        )

        # Sonneborn-Berger
        sb = 0.0
        for oid, res in zip(p.opponents, p.results):
            opp = by_id.get(oid)
            if opp is None:
                continue
            if res == "W":
                sb += opp.score
            elif res == "D":
                sb += opp.score / 2

        p.tiebreaks = {
            "mod_median": round(mod_median, 2),
            "solkoff": round(solkoff, 2),
            "cumulative": round(cumulative, 2),
            "opp_cumulative": round(opp_cumulative, 2),
            "sonneborn_berger": round(sb, 2),
        }


# ─── Standings ───────────────────────────────────────────────────────────────

def get_standings(players: list[Player], section_id: str) -> list[Player]:
    """Return sorted standings for a section. Tiebreaks must be computed first."""
    section_players = [p for p in players if p.section_id == section_id and not p.withdrawn]
    compute_tiebreaks(players)  # always recompute with latest scores
    section_players.sort(key=lambda p: (
        -p.score,
        -p.tiebreaks.get("mod_median", 0),
        -p.tiebreaks.get("solkoff", 0),
        -p.tiebreaks.get("cumulative", 0),
        -p.tiebreaks.get("opp_cumulative", 0),
    ))
    return section_players


# ─── Auto Section Assignment ─────────────────────────────────────────────────

def auto_assign_section(rating: int, sections: list[Section]) -> Optional[str]:
    """Assign player to the lowest (most restrictive) eligible section."""
    eligible = [s for s in sections if s.eligible(rating)]
    if not eligible:
        # Fall back to first open section
        open_sections = [s for s in sections if s.max_rating is None]
        return open_sections[0].id if open_sections else (sections[0].id if sections else None)
    # Sort by max_rating ascending (most restrictive first), None = Open (goes last)
    eligible.sort(key=lambda s: (s.max_rating is None, s.max_rating or 0))
    return eligible[0].id


# ─── Serialization ───────────────────────────────────────────────────────────

def save_tournament(filepath: str, tournament: Tournament, sections: list[Section],
                    players: list[Player], rounds: list[Round]) -> None:
    data = {
        "tournament": tournament.to_dict(),
        "sections": [s.to_dict() for s in sections],
        "players": [p.to_dict() for p in players],
        "rounds": [
            {
                "number": r.number,
                "pairings": [
                    {"white_id": p.white_id, "black_id": p.black_id, "result": p.result}
                    for p in r.pairings
                ],
                "byes": r.byes,
            }
            for r in rounds
        ],
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_tournament(filepath: str):
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    tournament = Tournament(**data["tournament"])
    sections = [Section.from_dict(s) for s in data["sections"]]
    players = [Player.from_dict(p) for p in data["players"]]
    rounds = [
        Round(
            number=r["number"],
            pairings=[Pairing(**p) for p in r["pairings"]],
            byes=r.get("byes", {}),
        )
        for r in data.get("rounds", [])
    ]
    return tournament, sections, players, rounds
