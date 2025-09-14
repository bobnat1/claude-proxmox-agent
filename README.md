# Proxmox VM Management Agent

A Python script that uses Claude AI to manage Proxmox Virtual Environment VMs through natural language commands.

## Features

- Interactive chat interface for VM management
- Command-line mode for single operations
- Uses Claude API with bash tool access
- Supports common Proxmox VM operations (start, stop, status, etc.)

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your Anthropic API key:
```bash
python3 proxmox_vm_agent.py setup
```

Or set the environment variable:
```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

## Usage

### Interactive Mode
```bash
python3 proxmox_vm_agent.py
```

### Command Mode
```bash
python3 proxmox_vm_agent.py "list all VMs"
python3 proxmox_vm_agent.py "start VM 100"
python3 proxmox_vm_agent.py "check status of VM 101"
```

## Supported Commands

The agent can execute various Proxmox commands:
- List VMs and containers
- Start/stop/shutdown/reboot VMs
- Check VM status
- Manage containers (LXC)
- Execute commands on VMs/containers with guest agent installed
- Check guest agent status
- Suspend VMs to disk/RAM via guest agent

## Configuration

Configuration is stored in `~/.config/claude-proxmox/config.json`

## Requirements

- Python 3.6+
- Proxmox VE environment
- Anthropic API key
- `requests` library