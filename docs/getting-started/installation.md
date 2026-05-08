# Installation

## Requirements

- Python 3.10+
- pip

## Install

```bash
pip install sentinelflux
```

Install with AI self-healing support (Mistral):

```bash
pip install sentinelflux[ai]
```

Install all optional extras:

```bash
pip install sentinelflux[all]
```

## Install browsers

```bash
playwright install chromium
# or all browsers:
playwright install
```

## Verify

```bash
sentinelflux doctor
```

This checks Python version, required packages, browser installation, and your config file.
