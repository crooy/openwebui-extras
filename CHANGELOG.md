# Changelog

# [Unreleased]
## automemory
### Added
- Nix flake for development environment
- Development tools setup (mypy, flake8, black)
- Proper Python package typing against OpenWebUI models
- Improved documentation

### Changed
- Moved from manual setup to Nix-based development environment
- Updated Python dependencies management
- Improved code organization

### Fixed
- Memory operation handling in auto-memory
- JSON parsing in memory relevance analysis
- Development environment reproducibility

# [Released]

# auto-memory
## v0.4
- Added LLM-based memory relevance, improved memory deduplication, better context handling

## v0.3
- Migrated to OpenWebUI v0.5, updated to use OpenAI API by default
- forked from caplescrest's auto-memory
