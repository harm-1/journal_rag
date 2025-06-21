#!/usr/bin/env python3
"""
Convert org-journal files to org-roam-dailies format
Handles proper UUID generation and date format conversion
"""

import os
import re
import uuid
from pathlib import Path
from typing import Dict, List, Tuple
import argparse


class OrgJournalToRoamConverter:
    def __init__(self, journal_dir: str, roam_dir: str):
        """
        Initialize converter

        Args:
            journal_dir: Directory containing org-journal files
            roam_dir: Directory for org-roam-dailies files
        """
        self.journal_dir = Path(journal_dir)
        self.roam_dir = Path(roam_dir)

        # Ensure roam directory exists
        self.roam_dir.mkdir(parents=True, exist_ok=True)

    def _parse_journal_filename(self, filename: str) -> str:
        """
        Convert YYYYMMDD format to YYYY-MM-DD

        Args:
            filename: Original filename (e.g., '20210604')

        Returns:
            Formatted date string (e.g., '2021-06-04')
        """
        # Remove extension if present
        base_name = filename.split(".")[0]

        # Check if it matches YYYYMMDD pattern
        if re.match(r"^\d{8}$", base_name):
            year = base_name[:4]
            month = base_name[4:6]
            day = base_name[6:8]
            return f"{year}-{month}-{day}"
        else:
            raise ValueError(f"Filename {filename} doesn't match YYYYMMDD pattern")

    def _parse_journal_content(self, content: str) -> Tuple[str, List[Tuple[str, str]]]:
        """
        Parse org-journal content and extract entries

        Args:
            content: Raw content of org-journal file

        Returns:
            Tuple of (date_header, list of (time, content) entries)
        """
        lines = content.strip().split("\n")
        date_header = ""
        entries = []
        current_time = ""
        current_content = []

        for line in lines:
            # Check for main date header (e.g., "* vrijdag, 04-06-21")
            if line.startswith("* ") and not re.match(r"^\*\* \d{2}:\d{2}", line):
                date_header = line[2:].strip()  # Remove "* "

            # Check for time entry (e.g., "** 09:22")
            elif line.startswith("** ") and re.match(r"^\*\* \d{2}:\d{2}", line):
                # Save previous entry if exists
                if current_time and current_content:
                    entries.append((current_time, "\n".join(current_content).strip()))

                # Start new entry
                current_time = line[3:].strip()  # Remove "** "
                current_content = []

            # Regular content line
            elif current_time:
                current_content.append(line)

        # Don't forget the last entry
        if current_time and current_content:
            entries.append((current_time, "\n".join(current_content).strip()))

        return date_header, entries

    def _generate_roam_content(self, date: str, entries: List[Tuple[str, str]]) -> str:
        """
        Generate org-roam-dailies formatted content

        Args:
            date: Date in YYYY-MM-DD format
            entries: List of (time, content) tuples

        Returns:
            Formatted org-roam content
        """
        # Generate a new UUID for this file
        file_id = str(uuid.uuid4())

        content = f""":PROPERTIES:
:ID:       {file_id}
:END:
#+title: {date}
"""

        # Add each time entry
        for time, entry_content in entries:
            content += f"* {time}\n"
            if entry_content:
                # Indent content properly
                indented_content = "\n".join(entry_content.split("\n"))
                content += f"{indented_content}\n"
            content += "\n"

        return content.rstrip() + "\n"

    def _check_existing_file(self, roam_file_path: Path) -> bool:
        """
        Check if org-roam file already exists and warn user

        Args:
            roam_file_path: Path to potential org-roam file

        Returns:
            True if file should be processed, False if skipped
        """
        if roam_file_path.exists():
            print(f"WARNING: {roam_file_path.name} already exists in org-roam-dailies")
            response = input("Overwrite? (y/N): ").strip().lower()
            return response in ["y", "yes"]
        return True

    def convert_file(self, journal_filename: str, dry_run: bool = False) -> bool:
        """
        Convert a single org-journal file to org-roam format

        Args:
            journal_filename: Name of the journal file to convert
            dry_run: If True, don't actually write files

        Returns:
            True if conversion was successful
        """
        journal_path = self.journal_dir / journal_filename

        if not journal_path.exists():
            print(f"ERROR: Journal file {journal_filename} not found")
            return False

        try:
            # Parse filename to get date
            roam_date = self._parse_journal_filename(journal_filename)
            roam_filename = f"{roam_date}.org"
            roam_path = self.roam_dir / roam_filename

            # Check if target file exists
            if not dry_run and not self._check_existing_file(roam_path):
                print(f"Skipping {journal_filename}")
                return True

            # Read and parse journal content
            with open(journal_path, "r", encoding="utf-8") as f:
                content = f.read()

            date_header, entries = self._parse_journal_content(content)

            # Generate org-roam content
            roam_content = self._generate_roam_content(roam_date, entries)

            if dry_run:
                print(f"Would convert: {journal_filename} -> {roam_filename}")
                print(f"  Date header: {date_header}")
                print(f"  Entries: {len(entries)}")
                print(f"  Preview:")
                print("  " + "\n  ".join(roam_content.split("\n")[:10]))
                if len(roam_content.split("\n")) > 10:
                    print("  ...")
                print()
            else:
                # Write org-roam file
                with open(roam_path, "w", encoding="utf-8") as f:
                    f.write(roam_content)

                print(f"Converted: {journal_filename} -> {roam_filename}")

            return True

        except Exception as e:
            print(f"ERROR converting {journal_filename}: {e}")
            return False

    def convert_all(self, dry_run: bool = False) -> Dict[str, int]:
        """
        Convert all org-journal files to org-roam format

        Args:
            dry_run: If True, don't actually write files

        Returns:
            Dictionary with conversion statistics
        """
        stats = {"total": 0, "successful": 0, "failed": 0, "skipped": 0}

        # Find all potential journal files
        journal_files = []
        for file_path in self.journal_dir.iterdir():
            if file_path.is_file():
                # Check if filename matches YYYYMMDD pattern
                base_name = file_path.stem
                if re.match(r"^\d{8}$", base_name):
                    journal_files.append(file_path.name)

        journal_files.sort()
        stats["total"] = len(journal_files)

        if not journal_files:
            print("No org-journal files found matching YYYYMMDD pattern")
            return stats

        print(f"Found {len(journal_files)} journal files to convert")
        if dry_run:
            print("DRY RUN - No files will be modified")
        print()

        for filename in journal_files:
            if self.convert_file(filename, dry_run):
                stats["successful"] += 1
            else:
                stats["failed"] += 1

        return stats

    def list_journal_files(self) -> List[str]:
        """List all org-journal files that can be converted"""
        journal_files = []
        for file_path in self.journal_dir.iterdir():
            if file_path.is_file():
                base_name = file_path.stem
                if re.match(r"^\d{8}$", base_name):
                    try:
                        roam_date = self._parse_journal_filename(file_path.name)
                        journal_files.append(f"{file_path.name} -> {roam_date}.org")
                    except ValueError:
                        continue

        return sorted(journal_files)


def main():
    parser = argparse.ArgumentParser(
        description="Convert org-journal files to org-roam-dailies format"
    )
    parser.add_argument(
        "journal_dir",
        nargs="?",
        help="Directory containing org-journal files",
        default="~/org/journal",
    )
    parser.add_argument(
        "roam_dir",
        nargs="?",
        help="Directory for org-roam-dailies files",
        default="~/org/roam/daily",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be converted without making changes",
    )
    parser.add_argument(
        "--list", action="store_true", help="List journal files that can be converted"
    )
    parser.add_argument("--file", type=str, help="Convert specific file only")

    args = parser.parse_args()

    journal_dir = os.path.expanduser(args.journal_dir)
    if not os.path.exists(journal_dir):
        print(f"ERROR: Journal directory {args.journal_dir} does not exist")
        return 1

    converter = OrgJournalToRoamConverter(
        journal_dir, os.path.expanduser(args.roam_dir)
    )

    if args.list:
        files = converter.list_journal_files()
        if files:
            print("Journal files that can be converted:")
            for file_mapping in files:
                print(f"  {file_mapping}")
        else:
            print("No convertible journal files found")
        return 0

    if args.file:
        success = converter.convert_file(args.file, args.dry_run)
        return 0 if success else 1

    # Convert all files
    stats = converter.convert_all(args.dry_run)

    print("\nConversion completed:")
    print(f"  Total files: {stats['total']}")
    print(f"  Successful: {stats['successful']}")
    print(f"  Failed: {stats['failed']}")

    if not args.dry_run and stats["successful"] > 0:
        print("\nIMPORTANT: After conversion, you should:")
        print("1. Run 'M-x org-roam-db-sync' in Emacs to update the org-roam database")
        print("2. Verify the converted files look correct")
        print("3. Consider backing up your original org-journal files")

    return 0


if __name__ == "__main__":
    exit(main())
