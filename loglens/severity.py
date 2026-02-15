"""
Severity level utilities for syslog/journald priorities.

Maps numeric priorities (0-7) to human-readable labels and vice versa.
"""

from typing import Union

# Syslog/journald priority levels (RFC 5424)
PRIORITY_LABELS = {
    0: "EMERG",
    1: "ALERT",
    2: "CRIT",
    3: "ERROR",
    4: "WARNING",
    5: "NOTICE",
    6: "INFO",
    7: "DEBUG",
}

# Reverse mapping for label -> number
LABEL_PRIORITIES = {label.lower(): num for num, label in PRIORITY_LABELS.items()}
# Add common aliases
LABEL_PRIORITIES.update({
    "err": 3,
    "warn": 4,
    "critical": 2,
    "emergency": 0,
})


def priority_to_label(priority: int) -> str:
    """
    Convert numeric priority to label.
    
    Args:
        priority: Numeric priority (0-7)
        
    Returns:
        Label string (e.g., "ERROR", "INFO")
        
    Raises:
        ValueError: If priority is out of range
    """
    if priority not in PRIORITY_LABELS:
        raise ValueError(f"Invalid priority: {priority}. Must be 0-7.")
    return PRIORITY_LABELS[priority]


def label_to_priority(label: Union[str, int]) -> int:
    """
    Convert label or numeric string to priority number.
    
    Args:
        label: Label string (case-insensitive) or numeric value
        
    Returns:
        Numeric priority (0-7)
        
    Raises:
        ValueError: If label is unknown or number is out of range
    """
    # Handle numeric input
    if isinstance(label, int):
        if 0 <= label <= 7:
            return label
        raise ValueError(f"Invalid priority number: {label}. Must be 0-7.")
    
    # Handle string numeric
    if label.isdigit():
        priority = int(label)
        if 0 <= priority <= 7:
            return priority
        raise ValueError(f"Invalid priority number: {label}. Must be 0-7.")
    
    # Handle label string
    label_lower = label.lower()
    if label_lower not in LABEL_PRIORITIES:
        raise ValueError(
            f"Unknown severity label: '{label}'. "
            f"Valid labels: {', '.join(sorted(set(LABEL_PRIORITIES.keys())))}"
        )
    return LABEL_PRIORITIES[label_lower]


def is_at_least_severity(priority: int, min_severity: Union[str, int]) -> bool:
    """
    Check if priority is at least as severe as min_severity.
    
    Lower numbers = more severe in syslog/journald.
    
    Args:
        priority: Numeric priority to check (0-7)
        min_severity: Minimum severity threshold (label or number)
        
    Returns:
        True if priority <= threshold (i.e., as severe or more severe)
    """
    threshold = label_to_priority(min_severity)
    return priority <= threshold
