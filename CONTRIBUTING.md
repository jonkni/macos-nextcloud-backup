# Contributing to macOS Nextcloud Backup

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Development Setup

### Prerequisites
- macOS 11.0 or later
- Python 3.9+
- Git

### Setting Up Your Environment

1. Fork and clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/macos-nextcloud-backup.git
cd macos-nextcloud-backup
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
pip install -e .  # Install in development mode
```

4. Run tests:
```bash
pytest
```

## Development Workflow

1. Create a new branch for your feature/fix:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes

3. Write tests for your changes

4. Ensure tests pass:
```bash
pytest
```

5. Format code:
```bash
black mnb/
flake8 mnb/
```

6. Commit your changes:
```bash
git commit -m "Description of changes"
```

7. Push to your fork:
```bash
git push origin feature/your-feature-name
```

8. Create a Pull Request

## Code Style

- Follow PEP 8
- Use `black` for formatting
- Use type hints where appropriate
- Write docstrings for public functions/classes
- Keep functions focused and small

## Testing

- Write unit tests for new features
- Ensure existing tests pass
- Aim for good code coverage
- Test on real Nextcloud instance when possible

## Areas for Contribution

### ✅ Completed Features

**Client-Side Encryption (AES-256-GCM)** ✅ **COMPLETE**
- ✅ Files encrypted before upload to protect sensitive data
- ✅ PBKDF2-HMAC-SHA256 key derivation (600,000 iterations)
- ✅ AES-256-GCM authenticated encryption
- ✅ Secure key storage in macOS Keychain
- ✅ Restore functionality with automatic decryption
- ✅ Authentication tag verification (tampering detection)
- **Project is now production-ready!**

### 🟡 High Priority - Core Improvements

- **Backup verification** - Verify uploaded file integrity after upload
- **Full snapshot restore** - Restore entire snapshots (not just individual files)
- **Error handling improvements** - Better retry logic for network failures
- **Performance optimization** - Streaming encryption for large files (reduce memory usage)
- **Documentation** - Improve setup guides, add troubleshooting

### 🟢 Medium Priority - Features

- **Multiple Nextcloud instances** - Backup to multiple destinations
- **Web dashboard** - Browser-based status/restore interface
- **Custom retention policies** - More flexible snapshot cleanup rules
- **Bandwidth monitoring** - Track upload/download statistics
- **GUI enhancements** - Visual status indicators, custom icons

### 🔵 Low Priority - Nice to Have

- **Compression** - Optional compression before upload
- **Multi-platform support** - Linux, Windows support
- **Alternative storage backends** - S3, other WebDAV servers
- **Advanced exclusion patterns** - More powerful filtering

### ✅ Completed - For Reference

The following areas have been implemented:
- ✅ WebDAV client with connection pooling and parallel uploads
- ✅ File scanner with exclusion patterns
- ✅ Incremental backup engine with metadata tracking
- ✅ Configuration management with Keychain integration
- ✅ Full CLI implementation
- ✅ launchd scheduling support
- ✅ Webhook notifications (Google Chat, Zabbix)
- ✅ macOS menu bar GUI application
- ✅ Network connectivity validation
- ✅ Backup locking mechanism

## Reporting Issues

When reporting issues, please include:
- macOS version
- Python version
- Full error message and stack trace
- Steps to reproduce
- Expected vs actual behavior

## Feature Requests

For feature requests:
- Check existing issues first
- Clearly describe the use case
- Explain why it would be useful
- Consider implementation complexity

## Questions?

Feel free to open an issue for questions or discussion!
