# Configuration Documentation

This folder contains PDF documentation files for CAN bus monitoring configurations.

## Important Note

The example files included (`configuration1_example.txt`, `configuration2_example.txt`) are **placeholder text files only**. The `configurations.json` file references PDF files (`configuration1.pdf`, `configuration2.pdf`) that should be created by users.

**To use this feature**, you must replace these placeholder files with actual PDF documents.

## Usage

To add documentation for a configuration:

1. Place your PDF file in this directory (e.g., `configuration1.pdf`)
2. Update the configuration in `configurations.json` with the `info_pdf` field:
   ```json
   {
     "name": "Configuration 1",
     "info_pdf": "config/docs/configuration1.pdf",
     "signals": [...]
   }
   ```
3. An info button (ℹ️) will appear next to the configuration in the selection screen
4. Clicking the button will open the PDF with your system's default PDF viewer

## Example Documentation Structure

```
config/docs/
├── README.md
├── configuration1.pdf
├── configuration2.pdf
└── test_configuration.pdf
```

## File Naming Convention

Use descriptive names that match your configuration names:
- `configuration1.pdf` - Documentation for "Configuration 1"
- `j1939_monitoring.pdf` - Documentation for J1939 configurations
- `custom_signals.pdf` - Documentation for custom signal configurations

## Notes

- The `info_pdf` field is optional - configurations without it won't show an info button
- Paths should be relative to the project root directory
- Supported format: PDF files only
- Files will be opened with the system's default PDF viewer
