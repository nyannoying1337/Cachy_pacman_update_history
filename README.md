# CachyUpdate History

A tool to parse and display Pacman package history in a clean, organized format. Makes it easy to view your system's package installation, upgrade, and removal history.

## Features

- Rich terminal display with formatted tables
- Date and time parsing from Pacman logs
- Filtering by date ranges, package names, and operation types
- Export functionality to save history to text files
- Multiple display modes (table, summary, detailed)
- Desktop notifications (optional)
- Fast performance for large log files
- Robust error handling
- Standalone executable option

## Requirements

### Python Script:
- Python 3.7+
- `rich` library (`pip install rich`)

### Standalone Executable:
- No additional requirements (self-contained)

## Installation

### Option 1: Python Script
```bash
# Clone the repository
git clone https://github.com/nyannoying1337/Cachy_pacman_update_history.git
cd Cachy_pacman_update_history

# Install dependencies
pip install rich

# Run the script
python3 CachyUpdate_History.py
```

### Option 2: Standalone Executable
```bash
# Download the executable from releases
# Make it executable
chmod +x CachyUpdate_History

# Run directly
./CachyUpdate_History
```

## Usage

### Basic Usage
```bash
# Display recent package history
python3 CachyUpdate_History.py

# Show help
python3 CachyUpdate_History.py --help
```

### Advanced Options
```bash
# Filter by date range
python3 CachyUpdate_History.py --start-date 2024-01-01 --end-date 2024-12-31

# Filter by package name
python3 CachyUpdate_History.py --package firefox

# Show only installations
python3 CachyUpdate_History.py --operation installed

# Export to file
python3 CachyUpdate_History.py --export pacman_history.txt

# Show last N entries
python3 CachyUpdate_History.py --limit 50
```

### Command Line Options
| Option | Description | Example |
|--------|-------------|---------|
| `--start-date` | Start date for filtering (YYYY-MM-DD) | `--start-date 2024-01-01` |
| `--end-date` | End date for filtering (YYYY-MM-DD) | `--end-date 2024-12-31` |
| `--package` | Filter by package name | `--package firefox` |
| `--operation` | Filter by operation type | `--operation installed` |
| `--limit` | Limit number of entries shown | `--limit 100` |
| `--export` | Export to text file | `--export history.txt` |
| `--no-notifications` | Disable desktop notifications | `--no-notifications` |
| `--help` | Show help message | `--help` |

## Output Example

```
┌─────────────────────┬─────────────────┬──────────────┬─────────────────┐
│ Date & Time         │ Operation       │ Package      │ Version         │
├─────────────────────┼─────────────────┼──────────────┼─────────────────┤
│ 2024-01-15 14:30:22 │ installed       │ firefox      │ 121.0-1         │
│ 2024-01-15 14:25:10 │ upgraded        │ linux        │ 6.7.1-1         │
│ 2024-01-15 14:20:05 │ removed         │ old-package  │ 1.0.0-1         │
└─────────────────────┴─────────────────┴──────────────┴─────────────────┘
```

## Configuration

The tool automatically detects your Pacman log file location. Common locations:
- `/var/log/pacman.log` (default)
- `/var/log/pacman.log.1` (rotated logs)

## Development

### Project Structure
```
CachyUpdate_History/
├── CachyUpdate_History.py    # Main script
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── .gitignore               # Git ignore rules
├── dist/                    # Compiled executable
└── venv/                    # Virtual environment
```

### Building from Source
```bash
# Set up development environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Build executable
pyinstaller --onefile CachyUpdate_History.py
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

If you encounter any issues or have questions:
1. Check the [Issues](https://github.com/nyannoying1337/Cachy_pacman_update_history/issues) page
2. Create a new issue with detailed information
3. Include your system information and error messages 