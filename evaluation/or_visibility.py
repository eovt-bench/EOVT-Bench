"""Current elapsed-time OR scoring; v0.1 remains explicitly versioned."""
from dataclasses import asdict
from or_current import Config as ORConfig, score_event, aggregate_events

def config_dict(config=None):
    return asdict(config or ORConfig())
