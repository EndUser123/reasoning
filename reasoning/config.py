"""
Configuration for reasoning engine.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from reasoning.models import Mode


@dataclass
class ReasoningConfig:
    """Configuration for ReasoningEngine."""

    # Core settings
    mode: Mode = Mode.SEQUENTIAL
    llm_provider: str = "claude"

    # Storage settings
    storage_backend: str = "memory"  # "memory" or "file"
    storage_path: str = "~/.reasoning/storage"

    # Processing limits
    max_thoughts: int = 50
    quality_threshold: float = 0.5

    # Logging
    enable_logging: bool = True
    log_level: str = "INFO"

    # Mode-specific settings
    multi_agent_config: dict[str, Any] = field(default_factory=dict)
    cognitive_config: dict[str, Any] = field(default_factory=dict)
    graph_config: dict[str, Any] = field(default_factory=dict)
    two_stage_config: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate and normalize configuration."""
        # Expand storage path
        if self.storage_backend == "file":
            self.storage_path = str(Path(self.storage_path).expanduser())

        # Validate log level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_log_levels:
            raise ValueError(f"Invalid log level: {self.log_level}")

        # Validate thresholds
        if not 0.0 <= self.quality_threshold <= 1.0:
            raise ValueError("Quality threshold must be between 0 and 1")

        if self.max_thoughts < 1:
            raise ValueError("Max thoughts must be positive")

    @classmethod
    def from_dict(cls, config_dict: dict[str, Any]) -> ReasoningConfig:
        """Create configuration from dictionary."""
        # Convert mode string to enum
        if "mode" in config_dict and isinstance(config_dict["mode"], str):
            config_dict["mode"] = Mode(config_dict["mode"])

        return cls(**config_dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "mode": self.mode.value,
            "llm_provider": self.llm_provider,
            "storage_backend": self.storage_backend,
            "storage_path": self.storage_path,
            "max_thoughts": self.max_thoughts,
            "quality_threshold": self.quality_threshold,
            "enable_logging": self.enable_logging,
            "log_level": self.log_level,
            "multi_agent_config": self.multi_agent_config,
            "cognitive_config": self.cognitive_config,
            "graph_config": self.graph_config,
            "two_stage_config": self.two_stage_config,
        }
