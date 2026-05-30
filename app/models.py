from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .extensions import db


class RealTeam(db.Model):
    __tablename__ = "real_teams"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    color: Mapped[str] = mapped_column(String(7), nullable=False)
    prefix: Mapped[str] = mapped_column(String(50), nullable=False, default="")

    players: Mapped[list[Player]] = relationship(back_populates="real_team")


class Player(db.Model):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(primary_key=True)
    display_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    real_team_id: Mapped[int | None] = mapped_column(ForeignKey("real_teams.id"), nullable=True)
    is_captain: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    account_name_override: Mapped[str | None] = mapped_column(String(50), nullable=True)

    real_team: Mapped[RealTeam | None] = relationship(back_populates="players")
    snapshots: Mapped[list[HiscoreSnapshot]] = relationship(
        back_populates="player", order_by="HiscoreSnapshot.snapped_at"
    )
    roster_entry: Mapped[RosterEntry | None] = relationship(back_populates="player", uselist=False)
    deaths: Mapped[list[Death]] = relationship(back_populates="player", order_by="Death.recorded_at")

    @property
    def account_name(self) -> str | None:
        if self.account_name_override:
            return self.account_name_override
        if self.real_team and self.real_team.prefix:
            return f"{self.real_team.prefix} {self.display_name}"
        return None


class League(db.Model):
    __tablename__ = "leagues"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(8), unique=True, nullable=False)
    commissioner_token: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    managers: Mapped[list[Manager]] = relationship(back_populates="league")
    draft_state: Mapped[DraftState | None] = relationship(back_populates="league", uselist=False)


class Manager(db.Model):
    __tablename__ = "managers"

    id: Mapped[int] = mapped_column(primary_key=True)
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    token: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    pick_position: Mapped[int | None] = mapped_column(Integer, nullable=True)

    league: Mapped[League] = relationship(back_populates="managers")
    roster_entries: Mapped[list[RosterEntry]] = relationship(
        back_populates="manager", order_by="RosterEntry.pick_number"
    )


class RosterEntry(db.Model):
    __tablename__ = "roster_entries"
    __table_args__ = (
        UniqueConstraint("manager_id", "player_id"),
        UniqueConstraint("player_id"),  # each player on exactly one roster
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    manager_id: Mapped[int] = mapped_column(ForeignKey("managers.id"), nullable=False)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)
    pick_number: Mapped[int] = mapped_column(Integer, nullable=False)
    drafted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    manager: Mapped[Manager] = relationship(back_populates="roster_entries")
    player: Mapped[Player] = relationship(back_populates="roster_entry")


class DraftState(db.Model):
    __tablename__ = "draft_states"

    id: Mapped[int] = mapped_column(primary_key=True)
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"), unique=True, nullable=False)
    current_pick: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    league: Mapped[League] = relationship(back_populates="draft_state")


class HiscoreSnapshot(db.Model):
    """One row per poll/snapshot per player. All stat columns default to 0."""

    __tablename__ = "hiscore_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)
    snapshot_type: Mapped[str] = mapped_column(String(20), nullable=False)
    snapped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # ── Skills ────────────────────────────────────────────────────────────────
    overall_xp: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    attack_xp: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    defence_xp: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    strength_xp: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    hitpoints_xp: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    ranged_xp: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    prayer_xp: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    magic_xp: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    cooking_xp: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    woodcutting_xp: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    fletching_xp: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    fishing_xp: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    firemaking_xp: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    crafting_xp: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    smithing_xp: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    mining_xp: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    herblore_xp: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    agility_xp: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    thieving_xp: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    slayer_xp: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    farming_xp: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    runecraft_xp: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    hunter_xp: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    construction_xp: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)

    # ── PvP ───────────────────────────────────────────────────────────────────
    pvp_kills: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # ── Deaths (manual entry — also stored on the snapshot for point-in-time queries) ──
    deaths_cumulative: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # ── Bosses: weight 5 ──────────────────────────────────────────────────────
    barrows_chests: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    wintertodt: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tempoross: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    guardians_of_the_rift: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    giant_mole: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    king_black_dragon: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    chaos_fanatic: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    chaos_elemental: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    scorpia: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    crazy_archaeologist: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    deranged_archaeologist: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # ── Bosses: weight 10 ─────────────────────────────────────────────────────
    kalphite_queen: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    kraken: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    thermonuclear_smoke_devil: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sarachnis: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    skotizo: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    dagannoth_prime: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    dagannoth_rex: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    dagannoth_supreme: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    zalcano: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # ── Bosses: weight 20 ─────────────────────────────────────────────────────
    abyssal_sire: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cerberus: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    corporeal_beast: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    general_graardor: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    commander_zilyana: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    kreearra: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    kril_tsutsaroth: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    grotesque_guardians: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # ── Bosses: weight 30 ─────────────────────────────────────────────────────
    zulrah: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    vorkath: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    alchemical_hydra: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    phantom_muspah: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    nex: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # ── Raids: 1pt each ───────────────────────────────────────────────────────
    chambers_of_xeric: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    theatre_of_blood: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tombs_of_amascut: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    player: Mapped[Player] = relationship(back_populates="snapshots")


class Death(db.Model):
    """Commissioner-entered cumulative death counts per player."""

    __tablename__ = "deaths"

    id: Mapped[int] = mapped_column(primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)
    cumulative_count: Mapped[int] = mapped_column(Integer, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    player: Mapped[Player] = relationship(back_populates="deaths")
