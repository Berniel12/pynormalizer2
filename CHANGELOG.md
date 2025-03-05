# Changelog

## [1.1.0] - 2023-03-05

### Added
- Enhanced offline translation using ArgosTranslate
- Detailed before/after comparison logging in `normalization_comparison.log`
- Translation statistics tracking and reporting
- Test mode for quality evaluation with `--test` flag
- New `test_normalize.py` script for small sample processing
- Docker support with test mode as default
- Report generation with `--output` parameter
- Made all scripts executable with proper shebang lines

### Changed
- Updated Dockerfile to make all scripts executable
- Improved error handling in translation module
- Enhanced logging with separate log files for each script
- Updated README with comprehensive usage instructions
- Added .gitignore file for Python projects

### Fixed
- Better handling of language detection edge cases
- Improved error recovery during translation model download
- Fixed command-line argument handling in all scripts

## [1.0.0] - 2023-03-01

### Added
- Initial release
- Support for 9 tender data sources
- Unified schema for normalized data
- Basic offline translation capabilities
- Supabase integration
- PostgreSQL direct connection support 