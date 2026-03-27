"""Polytopia tribe data: starting resources, units, techs, and strengths."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Tribe:
    name: str
    terrain: str
    starting_tech: str
    starting_unit: str
    special_ability: str
    starting_stars: int
    city_income: int  # base stars per city per turn
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    strategy_notes: str = ""

    # Priority tech paths (ordered by recommended research order)
    early_techs: List[str] = field(default_factory=list)
    mid_techs: List[str] = field(default_factory=list)


TRIBES: dict[str, Tribe] = {
    "xin-xi": Tribe(
        name="Xin-Xi",
        terrain="Mountain",
        starting_tech="Climbing",
        starting_unit="Warrior",
        special_ability="Climb over mountains without a road",
        starting_stars=5,
        city_income=2,
        strengths=["Defensive mountain positions", "Fast scouting via peaks", "Strong mid-game"],
        weaknesses=["Limited early expansion on flat terrain", "Relies on mountain proximity"],
        strategy_notes=(
            "Use Climbing to scout mountains early for resources and city sites. "
            "Prioritize founding cities near mountain clusters. "
            "Mountains give +1 defence bonus, so station units there when defending."
        ),
        early_techs=["Hunting", "Organisation", "Fishing"],
        mid_techs=["Smithery", "Construction", "Meditation"],
    ),
    "imperius": Tribe(
        name="Imperius",
        terrain="Plains",
        starting_tech="Organisation",
        starting_unit="Warrior",
        special_ability="Start with a city at level 2 (3-tile border)",
        starting_stars=5,
        city_income=2,
        strengths=["Balanced start", "Larger initial city", "Good food/farm combo"],
        weaknesses=["No unique mobility advantage"],
        strategy_notes=(
            "Organisation lets you build a City Wall early for extra defence. "
            "Leverage the wider city border to capture more resource tiles. "
            "Good all-around tribe; focus on rapid expansion in the first 5 turns."
        ),
        early_techs=["Farming", "Hunting", "Riding"],
        mid_techs=["Roads", "Construction", "Smithery"],
    ),
    "bardur": Tribe(
        name="Bardur",
        terrain="Forest",
        starting_tech="Hunting",
        starting_unit="Warrior",
        special_ability="Hunting yields extra food from animals",
        starting_stars=5,
        city_income=2,
        strengths=["Strong early economy", "Easy food generation", "Flexible tech path"],
        weaknesses=["Forests slow non-road movement"],
        strategy_notes=(
            "Hunt animals aggressively in the first 3 turns to grow your capital quickly. "
            "Animals respawn, so keep hunters near forests throughout the early game. "
            "Research Forestry for +1 income per forest tile around cities."
        ),
        early_techs=["Forestry", "Fishing", "Riding"],
        mid_techs=["Smithery", "Construction", "Roads"],
    ),
    "oumaji": Tribe(
        name="Oumaji",
        terrain="Desert",
        starting_tech="Riding",
        starting_unit="Rider",
        special_ability="Riders move 2 tiles and can attack on the same turn",
        starting_stars=5,
        city_income=2,
        strengths=["Very fast early expansion", "Rider rush potential", "Unpredictable mobility"],
        weaknesses=["Desert resources are sparse", "Riders fragile against ranged units"],
        strategy_notes=(
            "Rush expansion with Riders in the first 4 turns before opponents can wall up. "
            "Capture unclaimed cities quickly; speed is your primary advantage. "
            "Avoid early confrontation with Archery tribes — riders die to catapults."
        ),
        early_techs=["Trade", "Archery", "Roads"],
        mid_techs=["Chivalry", "Construction", "Navigation"],
    ),
    "kickoo": Tribe(
        name="Kickoo",
        terrain="Lake/Coast",
        starting_tech="Fishing",
        starting_unit="Warrior",
        special_ability="Start on a lake; water tiles generate food",
        starting_stars=5,
        city_income=2,
        strengths=["Strong coastal economy", "Easy water travel with early boats", "Good food"],
        weaknesses=["Land-locked maps reduce advantage"],
        strategy_notes=(
            "Research Sailing early to exploit water tiles and reach distant cities fast. "
            "Build Ports to generate extra income from water. "
            "On maps with lots of coast/lake, Kickoo snowballs hard by mid-game."
        ),
        early_techs=["Sailing", "Aquatism", "Hunting"],
        mid_techs=["Navigation", "Construction", "Smithery"],
    ),
    "hoodrick": Tribe(
        name="Hoodrick",
        terrain="Forest",
        starting_tech="Archery",
        starting_unit="Archer",
        special_ability="Archers deal +1 damage in forests",
        starting_stars=5,
        city_income=2,
        strengths=["Ranged advantage", "Strong defensive forests", "Good vs Rider/Warrior rushes"],
        weaknesses=["Archers weak vs Swordsmen up close", "Limited movement in dense forest"],
        strategy_notes=(
            "Station Archers just inside forest borders; opponents pay extra movement to reach them. "
            "Research Forestry for income and then Shields for defensive archers. "
            "Avoid open-field battles; lure enemies into your forests."
        ),
        early_techs=["Forestry", "Hunting", "Shields"],
        mid_techs=["Smithery", "Construction", "Roads"],
    ),
    "luxidoor": Tribe(
        name="Luxidoor",
        terrain="Plains",
        starting_tech=None,
        starting_unit="Warrior",
        special_ability="Start with 2 cities (capital at level 3) but no starting tech",
        starting_stars=10,
        city_income=2,
        strengths=["Wealthiest early game", "Two city income from turn 1", "Flexible tech"],
        weaknesses=["No free starting tech", "Must spend stars on first research"],
        strategy_notes=(
            "Spend your 10 stars on a tech that matches nearby resources (Farming near farms, "
            "Hunting near animals, Fishing near water). "
            "Use dual income to research faster than any other tribe by turn 3."
        ),
        early_techs=["Farming", "Hunting", "Organisation"],
        mid_techs=["Roads", "Construction", "Smithery"],
    ),
    "vengir": Tribe(
        name="Vengir",
        terrain="Snow/Ice",
        starting_tech="Forging",
        starting_unit="Swordsman",
        special_ability="Start with a Swordsman (strongest basic unit)",
        starting_stars=5,
        city_income=2,
        strengths=["Strongest early unit", "Forging gives Swordsmen and giant-killers"],
        weaknesses=["Cold/sparse starting terrain", "Expensive units"],
        strategy_notes=(
            "Your Swordsman beats any starting unit 1v1 — use it to capture a nearby city on turn 1. "
            "Research Smithery next for stronger units, then Construction for city growth. "
            "Vengir wins by dominating early skirmishes; never let momentum stall."
        ),
        early_techs=["Smithery", "Roads", "Organisation"],
        mid_techs=["Construction", "Shields", "Chivalry"],
    ),
    "zebasi": Tribe(
        name="Zebasi",
        terrain="Plains/Savanna",
        starting_tech="Farming",
        starting_unit="Warrior",
        special_ability="Farms produce extra food on adjacent tiles",
        starting_stars=5,
        city_income=2,
        strengths=["Rapid city growth", "High population cities", "Excellent mid-game income"],
        weaknesses=["Slow early game combat", "Needs many farm tiles nearby"],
        strategy_notes=(
            "Build Farms on every adjacent tile around your capital ASAP — each grows the city faster. "
            "Larger cities unlock more city improvements and stronger units. "
            "Pair Farming with Organisation for City Walls and extra defence on big cities."
        ),
        early_techs=["Organisation", "Irrigation", "Hunting"],
        mid_techs=["Roads", "Construction", "Smithery"],
    ),
    "ai-mo": Tribe(
        name="Ai-Mo",
        terrain="Mountain",
        starting_tech="Meditation",
        starting_unit="Warrior",
        special_ability="Meditation lets you build Temples for passive star income",
        starting_stars=5,
        city_income=2,
        strengths=["Passive income from Temples", "Strong late-game economy", "Mountain defence"],
        weaknesses=["Temples are expensive upfront", "Slow early expansion"],
        strategy_notes=(
            "Build a Temple in your capital by turn 2-3 for long-term star income. "
            "Climb mountains to scout city sites early, like Xin-Xi. "
            "Pair Meditation with Philosophy for double Temple income in the late game."
        ),
        early_techs=["Climbing", "Philosophy", "Hunting"],
        mid_techs=["Construction", "Smithery", "Roads"],
    ),
    "quetzali": Tribe(
        name="Quetzali",
        terrain="Jungle/Mountain",
        starting_tech="Shields",
        starting_unit="Defender",
        special_ability="Defender unit has high defence and 2-range zone-of-control",
        starting_stars=5,
        city_income=2,
        strengths=["Excellent defence", "Defenders block enemy movement", "Resilient vs rushes"],
        weaknesses=["Low offensive power", "Slow movement in jungle"],
        strategy_notes=(
            "Use Defenders to block chokepoints and funnel enemies into traps. "
            "Defenders pair perfectly with Catapults behind them — push the line forward slowly. "
            "Research Roads to compensate for jungle movement penalties."
        ),
        early_techs=["Climbing", "Roads", "Hunting"],
        mid_techs=["Smithery", "Construction", "Archery"],
    ),
    "yadakk": Tribe(
        name="Yadakk",
        terrain="Plains/Desert",
        starting_tech="Roads",
        starting_unit="Warrior",
        special_ability="Roads connect cities for instant star bonus; start with road network",
        starting_stars=5,
        city_income=2,
        strengths=["Fast troop movement", "City connection bonuses", "Flexible expansion"],
        weaknesses=["Road network costs stars to maintain initially"],
        strategy_notes=(
            "Connect every city you found with roads immediately — each connection gives +1 income. "
            "Use road speed to redeploy units across your empire quickly. "
            "Prioritize Trade after Roads to maximize connection bonuses."
        ),
        early_techs=["Trade", "Riding", "Organisation"],
        mid_techs=["Construction", "Smithery", "Navigation"],
    ),
    "polaris": Tribe(
        name="Polaris",
        terrain="Ice/Snow",
        starting_tech="Polarism",
        starting_unit="Ice Archer",
        special_ability="Can freeze water tiles to walk on; Mooni creates permanent ice",
        starting_stars=5,
        city_income=2,
        strengths=["Unique map manipulation", "Ice bridges for fast travel", "Good early ranged unit"],
        weaknesses=["Warm maps reduce ice advantage", "Ice Archer weaker than land archers"],
        strategy_notes=(
            "Use Mooni units to create ice bridges to distant islands or across lakes. "
            "Freeze water between your cities and enemy coasts for surprise landings. "
            "On cold/lake maps, Polaris has a massive mobility advantage."
        ),
        early_techs=["Aquatism", "Climbing", "Hunting"],
        mid_techs=["Navigation", "Construction", "Smithery"],
    ),
    "cymanti": Tribe(
        name="Cymanti",
        terrain="Swamp/Jungle",
        starting_tech="Mycelium",
        starting_unit="Shaman",
        special_ability="Fungus tiles spread poison; Hexapods move through any terrain",
        starting_stars=5,
        city_income=2,
        strengths=["Biological warfare (poison)", "Unique unit roster", "Terrain denial"],
        weaknesses=["Complex to play well", "Weak vs fire/bomb units"],
        strategy_notes=(
            "Spread Fungus across enemy movement corridors to poison their units. "
            "Hexapod is extremely fast — use it like Oumaji Riders for early scouting. "
            "Pair Mycelium with Forestry for swamp-to-forest conversions and extra income."
        ),
        early_techs=["Forestry", "Riding", "Archery"],
        mid_techs=["Smithery", "Construction", "Navigation"],
    ),
}


def get_tribe(name: str) -> Optional[Tribe]:
    """Return a Tribe by case-insensitive name, or None if not found."""
    key = name.lower().replace(" ", "-")
    return TRIBES.get(key)


def list_tribe_names() -> List[str]:
    """Return sorted list of all tribe names."""
    return sorted(t.name for t in TRIBES.values())
