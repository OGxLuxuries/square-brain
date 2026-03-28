"""
Polytopia strategy advisor: given a tribe and game state, recommend
the best action for the current turn (stars vs city borders, tech, etc.).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from .tribes import Tribe, get_tribe, list_tribe_names


# ---------------------------------------------------------------------------
# Game-state model
# ---------------------------------------------------------------------------

@dataclass
class GameState:
    """
    Snapshot of the player's current situation in a Polytopia game.

    Attributes
    ----------
    tribe_name : str
        The player's tribe (e.g. ``"bardur"``).
    turn : int
        Current turn number (1-indexed).
    stars : int
        Stars (currency) available this turn.
    cities : int
        Number of cities the player controls.
    city_level : int
        Average city level (1 = 2-tile border, 2 = 3-tile, etc.).
    has_tech : list[str]
        Techs already researched.
    opponent_distance : int
        Estimated turns until first contact with the nearest opponent (1–10).
    nearby_resources : list[str]
        Resource types visible near your cities (e.g. ``["forest", "fish"]``).
    image_context : str | None
        Optional description extracted from an uploaded screenshot.
    """

    tribe_name: str
    turn: int = 1
    stars: int = 5
    cities: int = 1
    city_level: int = 1
    has_tech: List[str] = field(default_factory=list)
    opponent_distance: int = 5
    nearby_resources: List[str] = field(default_factory=list)
    image_context: Optional[str] = None


# ---------------------------------------------------------------------------
# Recommendation model
# ---------------------------------------------------------------------------

@dataclass
class Recommendation:
    """A single strategic recommendation."""

    priority: str          # "high" | "medium" | "low"
    category: str          # "economy" | "expansion" | "military" | "tech" | "city"
    action: str            # Short label
    rationale: str         # Explanation
    stars_cost: int = 0    # 0 means no direct star cost

    def __str__(self) -> str:
        cost_str = f"  [{self.stars_cost}★]" if self.stars_cost else ""
        return (
            f"[{self.priority.upper()}] {self.category.capitalize()} — "
            f"{self.action}{cost_str}\n  → {self.rationale}"
        )


# ---------------------------------------------------------------------------
# Core advisor
# ---------------------------------------------------------------------------

class StrategyAdvisor:
    """
    Analyse a :class:`GameState` and return ordered :class:`Recommendation`
    objects for the current turn.
    """

    # Star costs (approximate Polytopia values)
    TECH_COST = 5
    CITY_WALL_COST = 2
    WORKSHOP_COST = 5
    SANCTUARY_COST = 4
    PORT_COST = 5
    MINE_COST = 5
    FARM_COST = 5
    FORGE_COST = 5
    SAWMILL_COST = 5
    WINDMILL_COST = 5
    TEMPLE_COST = 20
    WARRIOR_COST = 2
    ARCHER_COST = 3
    RIDER_COST = 3
    SWORDSMAN_COST = 5
    CATAPULT_COST = 8

    def __init__(self, state: GameState) -> None:
        self.state = state
        tribe = get_tribe(state.tribe_name)
        if tribe is None:
            available = ", ".join(list_tribe_names())
            raise ValueError(
                f"Unknown tribe '{state.tribe_name}'. "
                f"Available tribes: {available}"
            )
        self.tribe: Tribe = tribe

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def recommend(self) -> List[Recommendation]:
        """Return a list of recommendations sorted by priority."""
        recs: List[Recommendation] = []
        recs.extend(self._economy_recs())
        recs.extend(self._tech_recs())
        recs.extend(self._expansion_recs())
        recs.extend(self._military_recs())
        recs.extend(self._city_recs())
        return self._sort_recommendations(recs)

    def stars_vs_borders(self) -> Tuple[str, str]:
        """
        Decide whether to grow a city (expanding borders for more resource tiles)
        or hold stars for other actions.

        Returns
        -------
        choice : str
            ``"grow_city"`` or ``"hold_stars"``
        reason : str
            Human-readable explanation.
        """
        s = self.state
        # Heuristic thresholds
        # Always grow if we have enough stars and few cities
        if s.stars >= 12 and s.cities <= 2:
            return (
                "grow_city",
                f"You have {s.stars}★ and only {s.cities} city/cities. "
                "Growing borders unlocks more resource tiles and increases per-turn income.",
            )

        # If opponent is close, save stars for units
        if s.opponent_distance <= 2:
            return (
                "hold_stars",
                f"Opponent is only ~{s.opponent_distance} turns away. "
                "Hold stars to train defensive/offensive units rather than growing borders.",
            )

        # Early game: grow cities for income
        if s.turn <= 5 and s.stars >= 8:
            return (
                "grow_city",
                f"Turn {s.turn}: early game priority is income. "
                "Growing borders lets you exploit more resources and level up cities faster.",
            )

        # Mid-game: balance based on tech and cities
        if s.cities >= 3 and s.stars < 10:
            return (
                "hold_stars",
                f"You have {s.cities} cities generating income. "
                "Save stars for a key tech research rather than growing borders right now.",
            )

        # Default: favour border growth for resource access
        return (
            "grow_city",
            "Expanding city borders gives access to more resource tiles, "
            "increasing your long-term income and tech options.",
        )

    def best_next_tech(self) -> Optional[str]:
        """Return the single highest-priority unresearched tech for this tribe."""
        researched = {t.lower() for t in self.state.has_tech}
        for tech in self.tribe.early_techs + self.tribe.mid_techs:
            if tech.lower() not in researched:
                return tech
        return None

    def summary(self) -> str:
        """Return a printable summary of the top recommendations."""
        recs = self.recommend()
        choice, reason = self.stars_vs_borders()
        next_tech = self.best_next_tech()

        lines = [
            f"═══ Polytopia Strategy — {self.tribe.name} (Turn {self.state.turn}) ═══",
            f"Available stars : {self.state.stars}★",
            f"Cities          : {self.state.cities}  |  City level avg: {self.state.city_level}",
            "",
            f"★ STARS vs CITY BORDERS → {choice.upper().replace('_', ' ')}",
            f"  {reason}",
            "",
            "TOP RECOMMENDATIONS:",
        ]
        for i, rec in enumerate(recs[:5], 1):
            lines.append(f"  {i}. {rec}")
            lines.append("")

        if next_tech:
            lines += [
                f"NEXT TECH TO RESEARCH: {next_tech} ({self.TECH_COST}★)",
                f"  {self.tribe.strategy_notes}",
            ]
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Private recommendation generators
    # ------------------------------------------------------------------

    def _economy_recs(self) -> List[Recommendation]:
        recs = []
        s = self.state

        # Tribe-specific economy advice
        if "forest" in s.nearby_resources and "Forestry" not in s.has_tech:
            recs.append(Recommendation(
                priority="high", category="economy",
                action="Research Forestry",
                rationale="Forest tiles visible near cities — Forestry adds +1 star/forest/turn.",
                stars_cost=self.TECH_COST,
            ))

        if "fish" in s.nearby_resources and "Fishing" not in s.has_tech:
            recs.append(Recommendation(
                priority="high", category="economy",
                action="Research Fishing",
                rationale="Water tiles nearby — Fishing lets you build Ports for +2 income each.",
                stars_cost=self.TECH_COST,
            ))

        if "farm" in s.nearby_resources and "Farming" not in s.has_tech:
            recs.append(Recommendation(
                priority="high", category="economy",
                action="Research Farming",
                rationale="Farm tiles nearby — cultivate fields to grow cities faster.",
                stars_cost=self.TECH_COST,
            ))

        if "mountain" in s.nearby_resources and "Mining" not in s.has_tech:
            recs.append(Recommendation(
                priority="medium", category="economy",
                action="Research Mining",
                rationale="Mountains nearby — mines provide +2 stars each.",
                stars_cost=self.TECH_COST,
            ))

        if self.tribe.name == "Ai-Mo" and "Meditation" not in s.has_tech:
            recs.append(Recommendation(
                priority="high", category="economy",
                action="Build a Temple (requires Meditation)",
                rationale="Temples generate passive star income each turn — essential for Ai-Mo.",
                stars_cost=self.TEMPLE_COST,
            ))

        if self.tribe.name == "Yadakk" and s.cities > 1:
            recs.append(Recommendation(
                priority="high", category="economy",
                action="Connect cities with Roads",
                rationale="Each road connection between cities gives +1 income per turn for Yadakk.",
                stars_cost=0,
            ))

        return recs

    def _tech_recs(self) -> List[Recommendation]:
        recs = []
        s = self.state
        next_tech = self.best_next_tech()

        if next_tech and s.stars >= self.TECH_COST:
            recs.append(Recommendation(
                priority="high", category="tech",
                action=f"Research {next_tech}",
                rationale=(
                    f"Next priority tech for {self.tribe.name}. "
                    f"{self.tribe.strategy_notes[:120].rstrip()}..."
                ),
                stars_cost=self.TECH_COST,
            ))

        # Warn about no tech this turn
        if s.stars < self.TECH_COST:
            recs.append(Recommendation(
                priority="medium", category="tech",
                action="Save stars for next tech",
                rationale=(
                    f"You only have {s.stars}★ — save up to {self.TECH_COST}★ to research "
                    f"{next_tech or 'a tech'} next turn."
                ),
                stars_cost=0,
            ))
        return recs

    def _expansion_recs(self) -> List[Recommendation]:
        recs = []
        s = self.state

        if s.turn <= 6 and s.cities < 3:
            recs.append(Recommendation(
                priority="high", category="expansion",
                action="Scout and capture nearby villages",
                rationale=(
                    f"Turn {s.turn}: capturing 2–3 villages quickly is critical for income. "
                    f"Each city adds {self.tribe.city_income}★/turn base income."
                ),
                stars_cost=0,
            ))

        if s.opponent_distance <= 3 and s.cities < 3:
            recs.append(Recommendation(
                priority="high", category="expansion",
                action="Expand before opponent blocks you",
                rationale=(
                    f"Opponent is only {s.opponent_distance} turns away and you control "
                    f"{s.cities} city/cities. Capture neutral villages now before they are contested."
                ),
                stars_cost=0,
            ))

        if self.tribe.name == "Oumaji" and s.turn <= 4:
            recs.append(Recommendation(
                priority="high", category="expansion",
                action="Rider rush — capture 2 villages this turn",
                rationale=(
                    "Oumaji Riders move 2 tiles and attack in the same turn. "
                    "Turn 1-4 is the window to seize villages before opponents can defend."
                ),
                stars_cost=0,
            ))

        if self.tribe.name == "Vengir" and s.turn == 1:
            recs.append(Recommendation(
                priority="high", category="expansion",
                action="Attack nearest village with Swordsman",
                rationale=(
                    "Vengir starts with a Swordsman — the strongest basic unit. "
                    "Use it immediately to capture a village on turn 1."
                ),
                stars_cost=0,
            ))

        return recs

    def _military_recs(self) -> List[Recommendation]:
        recs = []
        s = self.state

        if s.opponent_distance <= 2:
            recs.append(Recommendation(
                priority="high", category="military",
                action="Train 2 Warriors / ranged units for defence",
                rationale=(
                    f"Opponent ~{s.opponent_distance} turns away — build a defensive line now. "
                    "Place units on chokepoints or high-ground tiles."
                ),
                stars_cost=self.WARRIOR_COST * 2,
            ))
        elif s.opponent_distance <= 4 and s.cities >= 2:
            recs.append(Recommendation(
                priority="medium", category="military",
                action="Train 1 scout unit",
                rationale=(
                    "Push a Warrior or Rider forward to scout the map edge. "
                    "Finding opponents early prevents surprise attacks."
                ),
                stars_cost=self.WARRIOR_COST,
            ))

        if self.tribe.name == "Hoodrick":
            recs.append(Recommendation(
                priority="medium", category="military",
                action="Position Archers inside forest tiles",
                rationale=(
                    "Hoodrick Archers gain +1 damage from forests. "
                    "Stay inside the treeline — opponents take extra movement cost to engage."
                ),
                stars_cost=0,
            ))

        if self.tribe.name == "Quetzali":
            recs.append(Recommendation(
                priority="medium", category="military",
                action="Place Defenders at chokepoints",
                rationale=(
                    "Quetzali Defenders have high defence and block enemy movement. "
                    "Station them at mountain passes or river crossings."
                ),
                stars_cost=0,
            ))

        return recs

    def _city_recs(self) -> List[Recommendation]:
        recs = []
        s = self.state

        # Growing city borders
        choice, reason = self.stars_vs_borders()
        if choice == "grow_city" and s.stars >= 4:
            recs.append(Recommendation(
                priority="high", category="city",
                action="Grow city borders",
                rationale=reason,
                stars_cost=4,
            ))

        # City Wall for defence
        if s.opponent_distance <= 3 and s.stars >= self.CITY_WALL_COST:
            recs.append(Recommendation(
                priority="medium", category="city",
                action="Build City Wall on capital",
                rationale=(
                    "City Wall doubles city HP and adds a fortification tile. "
                    f"Opponent is only {s.opponent_distance} turns away."
                ),
                stars_cost=self.CITY_WALL_COST,
            ))

        return recs

    # ------------------------------------------------------------------
    # Sorting
    # ------------------------------------------------------------------

    @staticmethod
    def _sort_recommendations(recs: List[Recommendation]) -> List[Recommendation]:
        order = {"high": 0, "medium": 1, "low": 2}
        return sorted(recs, key=lambda r: order.get(r.priority, 3))
