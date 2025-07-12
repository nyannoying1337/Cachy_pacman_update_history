#!/usr/bin/env python3
"""
CachyUpdate History - A tool to parse and display pacman package history.

This script reads the pacman log file, parses package installation/upgrade/removal
events, and displays them in a formatted way with the option to export to a text file.
"""

import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo
import argparse

try:
    import tkinter as tk
    from tkinter import messagebox
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


class Config:
    """Configuration constants for the application."""
    
    LOG_PATH = "/var/log/pacman.log"
    LOG_PATTERN = re.compile(
        r"\[(.*?)\] \[ALPM\] (installed|upgraded|removed) ([^\s]+) \((.*?)\)"
    )
    LOCAL_TZ = ZoneInfo("Europe/Berlin")  # Adjust if needed
    
    ACTION_ICONS = {
        "installed": "📦",
        "upgraded": "🔼", 
        "removed": "❌",
    }
    
    ACTION_COLORS = {
        "installed": "green",
        "upgraded": "yellow",
        "removed": "red",
    }


class PacmanLogParser:
    """Handles parsing of pacman log files."""
    
    def __init__(self, log_path: str = Config.LOG_PATH):
        self.log_path = log_path
        self.console = Console()
    
    def parse_log(self) -> List[Tuple[datetime, str, str, str]]:
        """
        Parse the pacman log file and extract package events.
        
        Returns:
            List of tuples containing (timestamp, action, package, version)
        """
        entries = []
        
        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                for line in f:
                    match = Config.LOG_PATTERN.search(line)
                    if match:
                        raw_time, action, package, version = match.groups()
                        timestamp = self._parse_timestamp(raw_time)
                        version_str = self._format_version(action, version)
                        entries.append((timestamp, action, package, version_str))
        except FileNotFoundError:
            self.console.print(f"[bold red]Error: Log file not found at {self.log_path}[/]")
            return []
        except PermissionError:
            self.console.print(f"[bold red]Error: Permission denied reading {self.log_path}[/]")
            return []
        except Exception as e:
            self.console.print(f"[bold red]Error reading log file: {e}[/]")
            return []
        
        # Sort by timestamp in descending order (newest first)
        return sorted(entries, key=lambda x: x[0], reverse=True)
    
    def _parse_timestamp(self, raw_time: str) -> datetime:
        """Parse timestamp string to datetime object."""
        try:
            # Try parsing with timezone first
            timestamp = datetime.strptime(raw_time, "%Y-%m-%dT%H:%M:%S%z")
        except ValueError:
            # If no timezone, assume local time
            timestamp = datetime.strptime(raw_time, "%Y-%m-%dT%H:%M:%S")
            timestamp = timestamp.replace(tzinfo=Config.LOCAL_TZ)
        
        # Convert to local timezone for consistent display
        return timestamp.astimezone(Config.LOCAL_TZ)
    
    def _format_version(self, action: str, version: str) -> str:
        """Format version string based on action type."""
        if action == "upgraded":
            from_version, to_version = version.split(" -> ")
            return f"{from_version} → {to_version}"
        return version


class FileManager:
    """Handles file operations and document folder detection."""
    
    @staticmethod
    def get_documents_folder() -> str:
        """Get the user's documents folder path."""
        try:
            result = subprocess.run(
                ["xdg-user-dir", "DOCUMENTS"], 
                capture_output=True, 
                text=True
            )
            path = result.stdout.strip()
            if path and os.path.isdir(path):
                return path
        except Exception:
            pass
        
        # Fallback to default documents folder
        return os.path.expanduser("~/Documents")
    
    @staticmethod
    def ensure_directory_exists(path: str) -> None:
        """Ensure a directory exists, creating it if necessary."""
        os.makedirs(path, exist_ok=True)


class HistoryExporter:
    """Handles exporting history data to text files."""
    
    def __init__(self):
        self.console = Console()
    
    def save_to_text_file(self, entries: List[Tuple[datetime, str, str, str]], 
                         filename: Optional[str] = None) -> str:
        """
        Save all entries to a text file with proper formatting.
        
        Args:
            entries: List of parsed log entries
            filename: Optional custom filename
            
        Returns:
            Path to the saved file
        """
        if filename is None:
            documents = FileManager.get_documents_folder()
            FileManager.ensure_directory_exists(documents)
            filename = os.path.join(documents, "pacman_history.txt")
        
        try:
            with open(filename, "w", encoding="utf-8") as f:
                self._write_header(f)
                self._write_entries(f, entries)
                self._write_overall_summary(f, entries)
            
            return filename
        except Exception as e:
            self.console.print(f"[bold red]Error saving file: {e}[/]")
            raise
    
    def _write_header(self, file) -> None:
        """Write the file header."""
        file.write("PACMAN UPDATE HISTORY\n")
        file.write("=" * 50 + "\n\n")
    
    def _write_entries(self, file, entries: List[Tuple[datetime, str, str, str]]) -> None:
        """Write all entries grouped by date."""
        daily_entries = self._group_entries_by_date(entries)
        sorted_dates = sorted(daily_entries.keys(), reverse=True)
        
        for date_str in sorted_dates:
            day_entries = daily_entries[date_str]
            day_entries.sort(key=lambda x: x[0], reverse=True)
            
            self._write_date_section(file, date_str, day_entries)
    
    def _group_entries_by_date(self, entries: List[Tuple[datetime, str, str, str]]) -> Dict[str, List]:
        """Group entries by date."""
        daily_entries = {}
        for timestamp, action, package, version in entries:
            date_str = timestamp.strftime("%Y-%m-%d")
            if date_str not in daily_entries:
                daily_entries[date_str] = []
            daily_entries[date_str].append((timestamp, action, package, version))
        return daily_entries
    
    def _write_date_section(self, file, date_str: str, day_entries: List[Tuple[datetime, str, str, str]]) -> None:
        """Write entries for a specific date."""
        file.write(f"DATE: {date_str}\n")
        file.write("-" * 30 + "\n")
        
        daily_counts = {"installed": 0, "upgraded": 0, "removed": 0}
        
        # Write entries
        for timestamp, action, package, version in day_entries:
            time_str = timestamp.strftime("%H:%M:%S")
            
            if action in daily_counts:
                daily_counts[action] += 1
            
            icon = Config.ACTION_ICONS.get(action, "❔")
            action_display = f"{icon} {action.upper()}"
            
            suspicious = "↓" in version or "downgrade" in version.lower()
            version_display = f"[DOWNGRADE] {version}" if suspicious else version
            
            file.write(f"{time_str} | {action_display:<15} | {package:<30} | {version_display}\n")
        
        # Write daily summary
        file.write("\nSUMMARY:\n")
        for act, count in daily_counts.items():
            if count > 0:
                icon = Config.ACTION_ICONS.get(act, "")
                file.write(f"  {icon} {act.capitalize()}: {count}\n")
        
        file.write("\n" + "=" * 50 + "\n\n")
    
    def _write_overall_summary(self, file, entries: List[Tuple[datetime, str, str, str]]) -> None:
        """Write overall summary statistics."""
        total_counts = {"installed": 0, "upgraded": 0, "removed": 0}
        for _, action, _, _ in entries:
            if action in total_counts:
                total_counts[action] += 1
        
        file.write("OVERALL SUMMARY:\n")
        file.write("-" * 20 + "\n")
        for act, count in total_counts.items():
            icon = Config.ACTION_ICONS.get(act, "")
            file.write(f"{icon} {act.capitalize()}: {count}\n")


class HistoryDisplay:
    """Handles displaying history data in the terminal."""
    
    def __init__(self):
        self.console = Console()
    
    def display_updates(self, entries: List[Tuple[datetime, str, str, str]]) -> None:
        """
        Display package updates in a formatted table.
        
        Args:
            entries: List of parsed log entries
        """
        if not entries:
            self.console.print("[bold yellow]No package changes found in pacman.log.[/]")
            return
        
        daily_entries = self._group_entries_by_date(entries)
        sorted_dates = sorted(daily_entries.keys(), reverse=True)
        
        for date_str in sorted_dates:
            day_entries = daily_entries[date_str]
            day_entries.sort(key=lambda x: x[0], reverse=True)
            
            self._display_date_section(date_str, day_entries)
    
    def _group_entries_by_date(self, entries: List[Tuple[datetime, str, str, str]]) -> Dict[str, List]:
        """Group entries by date."""
        daily_entries = {}
        for timestamp, action, package, version in entries:
            date_str = timestamp.strftime("%Y-%m-%d")
            if date_str not in daily_entries:
                daily_entries[date_str] = []
            daily_entries[date_str].append((timestamp, action, package, version))
        return daily_entries
    
    def _display_date_section(self, date_str: str, day_entries: List[Tuple[datetime, str, str, str]]) -> None:
        """Display entries for a specific date."""
        # Print date header
        panel = Panel(
            Text(date_str, justify="center", style="bold white on blue"), 
            expand=False
        )
        self.console.print(panel)
        
        # Create table
        table = Table(show_header=True, header_style="bold cyan", box=None, expand=True)
        table.add_column("Time", style="dim", width=10)
        table.add_column("Action", style="bold", width=14)
        table.add_column("Package", style="bold white")
        table.add_column("Version Info", style="dim")
        
        daily_counts = {"installed": 0, "upgraded": 0, "removed": 0}
        
        # Add entries to table
        for timestamp, action, package, version in day_entries:
            time_str = timestamp.strftime("%H:%M:%S")
            
            if action in daily_counts:
                daily_counts[action] += 1
            
            icon = Config.ACTION_ICONS.get(action, "❔")
            color = Config.ACTION_COLORS.get(action, "white")
            action_text = f"[{color}]{icon} {action.capitalize()}[/{color}]"
            
            suspicious = "↓" in version or "downgrade" in version.lower()
            version_display = f"[bold red]{version}[/bold red]" if suspicious else version
            
            table.add_row(time_str, action_text, package, version_display)
        
        # Print table
        self.console.print(table)
        
        # Print summary
        self._display_daily_summary(date_str, daily_counts)
    
    def _display_daily_summary(self, date_str: str, daily_counts: Dict[str, int]) -> None:
        """Display summary for a specific date."""
        summary_text = Text()
        for act, count in daily_counts.items():
            if count > 0:
                color = Config.ACTION_COLORS.get(act, "white")
                icon = Config.ACTION_ICONS.get(act, "")
                summary_text.append(f"{icon} {act.capitalize()}: {count}  ", style=color)
        
        if summary_text.plain:
            panel = Panel(
                summary_text, 
                title=f"Summary for {date_str}", 
                expand=False, 
                border_style="bright_blue"
            )
            self.console.print(panel)


class NotificationManager:
    """Handles user notifications and file opening."""
    
    def __init__(self):
        self.console = Console()
    
    def show_popup(self, filename: str) -> None:
        """
        Show a popup notification about the saved file.
        
        Args:
            filename: Path to the saved file
        """
        abs_path = os.path.abspath(filename)
        
        # Try zenity first
        if self._try_zenity_popup(abs_path):
            return
        
        # Try Tkinter as fallback
        if self._try_tkinter_popup(abs_path):
            return
        
        # Final fallback: print to console
        self._print_fallback_message(abs_path)
    
    def _try_zenity_popup(self, abs_path: str) -> bool:
        """Try to show popup using zenity."""
        zenity_path = shutil.which("zenity")
        if not zenity_path:
            return False
        
        try:
            cmd = [
                "zenity", "--question",
                "--title=Pacman History Exported",
                f"--text=History saved to:\n{abs_path}",
                "--ok-label=Open file",
                "--cancel-label=Ok"
            ]
            result = subprocess.run(cmd)
            if result.returncode == 0:
                self._open_file(abs_path)
            return True
        except Exception:
            return False
    
    def _try_tkinter_popup(self, abs_path: str) -> bool:
        """Try to show popup using Tkinter."""
        if not TKINTER_AVAILABLE or not os.environ.get("DISPLAY"):
            return False
        
        try:
            self._create_tkinter_popup(abs_path)
            return True
        except Exception:
            return False
    
    def _create_tkinter_popup(self, abs_path: str) -> None:
        """Create and show Tkinter popup."""
        def open_file():
            try:
                subprocess.Popen(["xdg-open", abs_path])
            except Exception:
                pass
            root.destroy()
        
        def close_popup():
            root.destroy()
        
        root = tk.Tk()
        root.title("Pacman History Exported")
        root.geometry("400x120")
        root.resizable(False, False)
        
        label = tk.Label(
            root, 
            text=f"History saved to:\n{abs_path}", 
            wraplength=380, 
            justify="center"
        )
        label.pack(pady=10)
        
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=5)
        
        file_btn = tk.Button(btn_frame, text="Open file", command=open_file, width=12)
        file_btn.pack(side="left", padx=10)
        
        ok_btn = tk.Button(btn_frame, text="Ok", command=close_popup, width=12)
        ok_btn.pack(side="right", padx=10)
        
        root.mainloop()
    
    def _open_file(self, filepath: str) -> None:
        """Open file with default application."""
        try:
            subprocess.Popen(["xdg-open", filepath])
        except Exception as e:
            self.console.print(f"[yellow]Warning: Could not open file: {e}[/]")
    
    def _print_fallback_message(self, abs_path: str) -> None:
        """Print fallback message to console."""
        self.console.print(f"[green]History saved to: {abs_path}[/]")
        self.console.print(f"[dim]To open the file: xdg-open '{abs_path}'[/]")


def filter_entries(entries, start_date=None, end_date=None, package=None, operation=None, limit=None):
    filtered = []
    for entry in entries:
        timestamp, action, pkg, version = entry
        if start_date and timestamp.date() < start_date:
            continue
        if end_date and timestamp.date() > end_date:
            continue
        if package and package.lower() not in pkg.lower():
            continue
        if operation and action != operation:
            continue
        filtered.append(entry)
    if limit:
        filtered = filtered[:limit]
    return filtered


def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(description="Parse and display pacman package history.")
    parser.add_argument("--start-date", type=str, help="Start date for filtering (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, help="End date for filtering (YYYY-MM-DD)")
    parser.add_argument("--package", type=str, help="Filter by package name")
    parser.add_argument("--operation", type=str, choices=["installed", "upgraded", "removed"], help="Filter by operation type")
    parser.add_argument("--limit", type=int, help="Limit number of entries shown")
    parser.add_argument("--export", type=str, help="Export to text file")
    parser.add_argument("--no-notifications", action="store_true", help="Disable desktop notifications")
    args = parser.parse_args()

    try:
        # Parse pacman log
        log_parser = PacmanLogParser()
        entries = log_parser.parse_log()

        if not entries:
            print("No package changes found in pacman.log")
            return

        # Parse date arguments
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d").date() if args.start_date else None
        end_date = datetime.strptime(args.end_date, "%Y-%m-%d").date() if args.end_date else None
        package = args.package
        operation = args.operation
        limit = args.limit

        # Filter entries
        filtered_entries = filter_entries(entries, start_date, end_date, package, operation, limit)

        # Export to file if requested
        if args.export:
            exporter = HistoryExporter()
            filename = exporter.save_to_text_file(filtered_entries, args.export)
            if not args.no_notifications:
                notifier = NotificationManager()
                notifier.show_popup(filename)
            else:
                print(f"History saved to: {filename}")

        # Display in terminal
        display = HistoryDisplay()
        display.display_updates(filtered_entries)

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
