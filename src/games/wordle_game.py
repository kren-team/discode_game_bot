from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class LetterState(Enum):
    """State of a single letter in a Wordle guess."""

    CORRECT = "🟩"   # Right letter, right position
    PRESENT = "🟨"   # Right letter, wrong position
    ABSENT = "⬛"    # Letter not in the word

    @property
    def emoji(self) -> str:
        return self.value


@dataclass
class GuessResult:
    """Result of a single guess attempt."""

    word: str
    states: list[LetterState]

    def is_correct(self) -> bool:
        """Return True if every letter is in the correct position."""
        return all(s == LetterState.CORRECT for s in self.states)

    def to_display(self) -> str:
        """Return a string like 'C🟨 R⬛ A🟩 N🟩 E⬛'."""
        parts: list[str] = []
        for letter, state in zip(self.word, self.states):
            parts.append(f"{letter}{state.emoji}")
        return " ".join(parts)


class PlayerState(Enum):
    PLAYING = "playing"
    WON = "won"
    LOST = "lost"


@dataclass
class Player:
    """Represents a participant in the Wordle game."""

    user_id: int
    display_name: str
    guesses: list[GuessResult] = field(default_factory=list)
    state: PlayerState = PlayerState.PLAYING

    @property
    def guess_count(self) -> int:
        return len(self.guesses)

    def is_active(self) -> bool:
        return self.state == PlayerState.PLAYING

    def record_guess(self, result: GuessResult, max_guesses: int) -> None:
        """Record a guess result and update player state."""
        self.guesses.append(result)
        if result.is_correct():
            self.state = PlayerState.WON
        elif len(self.guesses) >= max_guesses:
            self.state = PlayerState.LOST


class GamePhase(Enum):
    RECRUITING = "recruiting"
    PLAYING = "playing"
    ENDED = "ended"


class WordleGame:
    """Core Wordle game state and logic."""

    MAX_GUESSES: int = 5
    WORD_LENGTH: int = 5

    def __init__(self, host_id: int, channel_id: int) -> None:
        self.host_id: int = host_id
        self.channel_id: int = channel_id
        self.word: str = ""
        self.players: dict[int, Player] = {}
        self.phase: GamePhase = GamePhase.RECRUITING

    # ------------------------------------------------------------------
    # Player management
    # ------------------------------------------------------------------

    def add_player(self, user_id: int, display_name: str) -> bool:
        """
        Add a player to the game during recruiting phase.

        Returns True if the player was added, False if already in the game
        or the game is not in recruiting phase.
        """
        if self.phase != GamePhase.RECRUITING:
            return False
        if user_id in self.players:
            return False
        self.players[user_id] = Player(user_id=user_id, display_name=display_name)
        return True

    def has_player(self, user_id: int) -> bool:
        return user_id in self.players

    # ------------------------------------------------------------------
    # Game lifecycle
    # ------------------------------------------------------------------

    def start(self, word: str) -> None:
        """Transition the game from RECRUITING to PLAYING with the given answer word."""
        if self.phase != GamePhase.RECRUITING:
            raise RuntimeError("Game is not in recruiting phase.")
        if not self.players:
            raise RuntimeError("Cannot start a game with no players.")
        self.word = word.upper()
        self.phase = GamePhase.PLAYING

    def check_guess(self, user_id: int, guess: str) -> Optional[GuessResult]:
        """
        Process a guess for a player.

        Returns the GuessResult, or None if the player cannot guess
        (wrong phase, not in game, already finished).
        """
        if self.phase != GamePhase.PLAYING:
            return None
        player = self.players.get(user_id)
        if player is None or not player.is_active():
            return None

        guess = guess.upper()
        states = self._evaluate_guess(guess)
        result = GuessResult(word=guess, states=states)
        player.record_guess(result, self.MAX_GUESSES)

        if self.is_game_over():
            self.phase = GamePhase.ENDED

        return result

    def _evaluate_guess(self, guess: str) -> list[LetterState]:
        """
        Two-pass Wordle evaluation algorithm.

        Pass 1: Mark exact matches (CORRECT).
        Pass 2: For remaining letters, mark PRESENT if the letter exists
                elsewhere in the answer (accounting for counts), else ABSENT.
        """
        states: list[LetterState] = [LetterState.ABSENT] * self.WORD_LENGTH
        answer_remaining: list[Optional[str]] = list(self.word)

        # Pass 1: exact matches
        for i, (g, a) in enumerate(zip(guess, self.word)):
            if g == a:
                states[i] = LetterState.CORRECT
                answer_remaining[i] = None  # consume this letter

        # Pass 2: present but wrong position
        for i, g in enumerate(guess):
            if states[i] == LetterState.CORRECT:
                continue
            if g in answer_remaining:
                states[i] = LetterState.PRESENT
                # Consume the first occurrence to avoid double-counting
                answer_remaining[answer_remaining.index(g)] = None

        return states

    # ------------------------------------------------------------------
    # Status queries
    # ------------------------------------------------------------------

    def is_game_over(self) -> bool:
        """Return True when no player is still in PLAYING state."""
        return all(not p.is_active() for p in self.players.values())

    def get_scoreboard(self) -> list[Player]:
        """
        Return players sorted for display:
        winners first (fewest guesses), then losers.
        """
        winners = [p for p in self.players.values() if p.state == PlayerState.WON]
        losers = [p for p in self.players.values() if p.state == PlayerState.LOST]
        still_playing = [p for p in self.players.values() if p.state == PlayerState.PLAYING]

        winners.sort(key=lambda p: p.guess_count)
        return winners + still_playing + losers

    def get_winner(self) -> Optional[Player]:
        """Return the player who won with the fewest guesses, or None."""
        winners = [p for p in self.players.values() if p.state == PlayerState.WON]
        if not winners:
            return None
        return min(winners, key=lambda p: p.guess_count)
