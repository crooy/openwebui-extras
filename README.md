# OpenWebUI Functions

> All functions in this repository can be found at [github.com/crooy/opewebui-extras](https://github.com/crooy/opewebui-extras)

For detailed version history, see [CHANGELOG.md](CHANGELOG.md)

## Development

### Setup
Using Nix Flake (recommended):
```bash
# Enable flakes in your nix configuration

# Enter development shell
nix develop

# Or use direnv with flakes
direnv allow
```

Manual setup:
```bash
pip install -r requirements-dev.txt
```

### Linting
```bash
mypy .
flake8 .
black .
```

The code is typed against the OpenWebUI models by installing the package as a dev dependency.

## Memory Management Functions

### Auto Memory
Automatically identifies and stores important information from user messages. Uses OpenAI's API to:
- Detect memorable information from user messages
- Retrieve relevant memories based on context
- Avoid storing duplicate memories
- Add memory context to conversations

### Add Memories
Allows manual saving of conversation snippets to memory.
- Stores both user message and assistant response
- Provides status updates during memory operations
- Handles errors gracefully with user feedback

## Configuration
Both memory functions can be configured through their respective valve settings:
- Enable/disable functionality
- Adjust OpenAI API settings (auto-memory)
- Control number of related memories to include
- Set memory relevance thresholds

## Repository
All code is available at [github.com/crooy/opewebui-extras](https://github.com/crooy/opewebui-extras). Feel free to:
- Submit issues
- Create pull requests
- Fork the repository
- Contribute improvements

## Development Status
This project is in active development. See [CHANGELOG.md](CHANGELOG.md) for recent changes.
