# OpenWebUI Functions Collection

A collection of utility functions for enhancing OpenWebUI's capabilities.

## Functions

### 1. Artifacts
**File:** `functions/artifacts.py`
- Displays HTML, CSS, and JavaScript code with an interactive viewer
- Features responsive design controls (mobile/tablet/desktop)
- Supports multiple artifacts in a single message
- Allows code editing and preview
- Version: 3.0.0 (OpenWebUI v0.5 compatible)

### 2. Auto-Memory
**File:** `functions/auto-memory.py`
- Automatically extracts and stores important information from conversations
- Updates existing memories instead of creating duplicates
- Uses OpenAI API for memory processing
- Configurable memory distance and relation settings
- Version: 0.3.0 (OpenWebUI v0.5 compatible)

### 3. Add Memories
**File:** `functions/add-memories.py`
- Adds action button to manually save messages to memory
- Simple one-click memory storage
- Shows status notifications
- Version: 0.3.0 (OpenWebUI v0.5 compatible)

### 4. Thinking Claude
**File:** `functions/thinking-claude.py`
- Enhances LLM responses with structured thinking process
- Auto-detects required thinking depth (quick/balanced/comprehensive)
- Supports custom thinking prompts
- Shows thinking process optionally
- Version: 0.15 (OpenWebUI v0.5 compatible)

## Installation

1. Copy the desired function files to your OpenWebUI functions directory
2. Restart OpenWebUI to load the new functions
3. Configure the functions through the UI valves (settings)

## Requirements

- OpenWebUI v0.5 or above
- OpenAI API access for memory and thinking functions
- Internet connection for API calls

## Configuration

Each function has configurable valves accessible through the OpenWebUI interface:

- **Artifacts:**
  - Enable/disable artifact processing
  - Show/hide status notifications

- **Auto-Memory:**
  - OpenAI API settings
  - Memory relation settings
  - Enable/disable auto-memory
  - Show/hide status notifications

- **Add Memories:**
  - Enable/disable memory button
  - Show/hide status notifications

- **Thinking Claude:**
  - Thinking depth control
  - Show/hide thinking process
  - Custom prompt support
  - OpenAI API settings

## Contributing

Feel free to submit issues, fork the repository and create pull requests for any improvements.

## Authors

- helloworldwastaken
- Peter De-Ath
- atgehrhardt
- tokyohouseparty
- Taosong Fang
- fangtaosong
- llm-sys
- constfrost

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenWebUI team for the core platform
- All contributors who helped improve these functions
