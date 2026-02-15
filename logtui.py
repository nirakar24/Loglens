#!/usr/bin/env python3
"""
LogLens TUI Entry Point.

Launch the Textual-based log viewer.

Usage:
    python3 logtui.py                          # View journalctl logs
    python3 logtui.py --since=-1h              # Last hour
    python3 logtui.py --units=sshd.service     # Specific unit
    python3 logtui.py --file=/var/log/syslog   # View file logs
"""

import sys
import argparse
from pathlib import Path

# Add loglens to path
sys.path.insert(0, str(Path(__file__).parent))

from loglens.tui.app import run_tui


def main():
    """Parse arguments and launch TUI."""
    parser = argparse.ArgumentParser(
        description="LogLens - Linux log viewer TUI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           View journalctl logs
  %(prog)s --since=-1h               View logs from last hour
  %(prog)s --since=-30m --priority=3 View ERROR and above from last 30 min
  %(prog)s --units=sshd.service      View logs from SSH service (systemd unit)
  %(prog)s --file=/var/log/syslog    View file-based logs
  
Note: To filter by non-unit sources like 'kernel', use the sidebar in the TUI 
(left panel shows all categories). The --units flag only works with systemd units.
        """
    )
    
    # Source selection
    source_group = parser.add_mutually_exclusive_group()
    source_group.add_argument(
        '--file',
        metavar='PATH',
        help='Read from file instead of journalctl'
    )
    source_group.add_argument(
        '--mode',
        choices=['text', 'jsonl'],
        help='File mode (requires --file)'
    )
    
    # Journalctl options
    parser.add_argument(
        '--since',
        metavar='TIME',
        help='Show logs since time (e.g., -1h, -30m, "2024-01-01")'
    )
    parser.add_argument(
        '--until',
        metavar='TIME',
        help='Show logs until time'
    )
    parser.add_argument(
        '--units',
        metavar='UNIT',
        nargs='+',
        help='Filter by systemd units (e.g., sshd.service, user@1000.service). Note: Use sidebar in TUI to filter by all categories including non-unit sources like "kernel"'
    )
    parser.add_argument(
        '--priority',
        metavar='NUM',
        type=int,
        choices=range(8),
        help='Maximum priority level (0=EMERG to 7=DEBUG)'
    )
    
    args = parser.parse_args()
    
    # Build source kwargs
    source_kwargs = {}
    
    if args.file:
        source = 'file'
        source_kwargs['path'] = args.file
        source_kwargs['mode'] = args.mode or 'text'
    else:
        source = 'journalctl'
        
        if args.since:
            source_kwargs['since'] = args.since
        if args.until:
            source_kwargs['until'] = args.until
        if args.units:
            source_kwargs['units'] = args.units
        if args.priority is not None:
            source_kwargs['priority'] = args.priority
    
    # Run TUI
    try:
        run_tui(source=source, **source_kwargs)
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
