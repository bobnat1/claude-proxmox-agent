#!/usr/bin/env python3
"""
Proxmox VM Management Agent using Claude API
A script that uses Claude's bash tool to manage Proxmox VMs
"""

import os
import json
import requests
import sys
from typing import Dict, List, Optional

class ProxmoxClaudeAgent:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://api.anthropic.com/v1/messages"
        self.headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        }
        self.conversation_history = []

    def send_message_to_claude(self, message: str) -> Dict:
        """Send message to Claude API with bash tool access"""

        system_prompt = """You are a Proxmox VM management assistant. You have access to the bash tool and should use it to help manage Proxmox VMs.

Key Proxmox commands you should know:
- pvesh get /nodes - list nodes
- pvesh get /nodes/{node}/qemu - list VMs on a node
- pvesh get /nodes/{node}/qemu/{vmid}/status/current - get VM status
- pvesh create /nodes/{node}/qemu/{vmid}/status/start - start VM
- pvesh create /nodes/{node}/qemu/{vmid}/status/stop - stop VM
- pvesh create /nodes/{node}/qemu/{vmid}/status/shutdown - shutdown VM
- pvesh create /nodes/{node}/qemu/{vmid}/status/reboot - reboot VM
- qm list - list all VMs
- qm status {vmid} - get VM status
- qm start {vmid} - start VM
- qm stop {vmid} - stop VM
- qm shutdown {vmid} - shutdown VM
- qm reboot {vmid} - reboot VM
- pct list - list containers
- pct status {vmid} - get container status
- pct start {vmid} - start container
- pct stop {vmid} - stop container

Guest Agent commands (for VMs/containers with Proxmox guest agent installed):
- qm guest exec {vmid} [username] -- {command} - execute command on VM
- qm guest passwd {vmid} {username} - set user password on VM
- pct exec {vmid} -- {command} - execute command on container
- pvesh create /nodes/{node}/qemu/{vmid}/agent/exec -- command="{command}" - execute via API
- pvesh get /nodes/{node}/qemu/{vmid}/agent/info - check if agent is running
- pvesh create /nodes/{node}/qemu/{vmid}/agent/shutdown - shutdown via agent
- pvesh create /nodes/{node}/qemu/{vmid}/agent/suspend-disk - suspend to disk
- pvesh create /nodes/{node}/qemu/{vmid}/agent/suspend-ram - suspend to RAM

Always use the bash tool to execute these commands and provide helpful, concise responses about VM management tasks."""

        payload = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 2000,
            "system": system_prompt,
            "messages": self.conversation_history + [{"role": "user", "content": message}],
            "tools": [
                {
                    "name": "bash",
                    "description": "Execute bash commands on the Proxmox system",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "The bash command to execute"
                            }
                        },
                        "required": ["command"]
                    }
                }
            ]
        }

        try:
            response = requests.post(self.api_url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"API request failed: {str(e)}"}

    def process_claude_response(self, response: Dict) -> str:
        """Process Claude's response and execute any bash commands"""
        if "error" in response:
            return f"❌ Error: {response['error']}"

        try:
            content = response["content"]
            result_text = ""

            for block in content:
                if block["type"] == "text":
                    result_text += block["text"] + "\n"
                elif block["type"] == "tool_use":
                    if block["name"] == "bash":
                        command = block["input"]["command"]
                        print(f"🔧 Executing: {command}")

                        # Execute the bash command
                        import subprocess
                        try:
                            result = subprocess.run(
                                command,
                                shell=True,
                                capture_output=True,
                                text=True,
                                timeout=30
                            )

                            tool_result = {
                                "type": "tool_result",
                                "tool_use_id": block["id"],
                                "content": f"Exit code: {result.returncode}\nStdout: {result.stdout}\nStderr: {result.stderr}"
                            }

                            # Send tool result back to Claude
                            self.conversation_history.append({"role": "user", "content": [tool_result]})

                            if result.returncode == 0:
                                result_text += f"✅ Command successful:\n{result.stdout}\n"
                            else:
                                result_text += f"❌ Command failed (exit {result.returncode}):\n{result.stderr}\n"

                        except subprocess.TimeoutExpired:
                            result_text += "⏰ Command timed out\n"
                        except Exception as e:
                            result_text += f"❌ Error executing command: {str(e)}\n"

            return result_text.strip()

        except Exception as e:
            return f"❌ Error processing response: {str(e)}"

    def chat(self, message: str) -> str:
        """Send a message to Claude and return the response"""
        self.conversation_history.append({"role": "user", "content": message})

        response = self.send_message_to_claude(message)
        result = self.process_claude_response(response)

        if not result.startswith("❌"):
            self.conversation_history.append({"role": "assistant", "content": result})

        return result

    def interactive_mode(self):
        """Run in interactive chat mode"""
        print("🤖 Proxmox VM Manager - Claude Agent")
        print("Type 'exit' to quit, 'clear' to clear history")
        print("=" * 50)

        while True:
            try:
                user_input = input("\n🔥 You: ").strip()

                if user_input.lower() == 'exit':
                    print("👋 Goodbye!")
                    break
                elif user_input.lower() == 'clear':
                    self.conversation_history = []
                    print("🧹 Conversation history cleared")
                    continue
                elif not user_input:
                    continue

                print("\n🤖 Claude:")
                response = self.chat(user_input)
                print(response)

            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {str(e)}")

def load_config():
    """Load configuration from file or environment"""
    config_file = os.path.expanduser("~/.config/claude-proxmox/config.json")

    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading config: {e}")

    # Fallback to environment variable
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if api_key:
        return {'api_key': api_key}

    return None

def create_config():
    """Create configuration file"""
    config_dir = os.path.expanduser("~/.config/claude-proxmox")
    config_file = os.path.join(config_dir, "config.json")

    api_key = input("Enter your Anthropic API key: ").strip()

    os.makedirs(config_dir, exist_ok=True)

    config = {'api_key': api_key}

    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"✅ Configuration saved to {config_file}")
        return config
    except Exception as e:
        print(f"❌ Error saving config: {e}")
        return None

def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'setup':
        create_config()
        return

    config = load_config()

    if not config or 'api_key' not in config:
        print("❌ No API key found. Run 'python3 proxmox_vm_agent.py setup' to configure.")
        return

    agent = ProxmoxClaudeAgent(config['api_key'])

    if len(sys.argv) > 1:
        # Command mode
        command = ' '.join(sys.argv[1:])
        response = agent.chat(command)
        print(response)
    else:
        # Interactive mode
        agent.interactive_mode()

if __name__ == "__main__":
    main()