#!/usr/bin/env python3
"""
Simple Claude CLI - A command-line interface for Claude Agent API.

This CLI allows you to interact with Claude in an agentic mode where it can
execute local commands (bash, git, rg, gh, curl, etc.) to accomplish coding tasks.
"""

import os
import sys
import json
import subprocess
from typing import Any, Dict, List
from anthropic import Anthropic


class ClaudeAgentCLI:
    """CLI for interacting with Claude using tool calling."""
    
    def __init__(
        self, 
        api_key: str = None, 
        model: str = "claude-3-7-sonnet-20250219",
        command_timeout: int = 300
    ):
        """Initialize the CLI with API credentials.
        
        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Claude model to use
            command_timeout: Timeout in seconds for bash command execution (default: 300)
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable must be set or provide api_key"
            )
        
        self.client = Anthropic(api_key=self.api_key)
        self.model = model
        self.command_timeout = command_timeout
        self.conversation_history: List[Dict[str, Any]] = []
        self.system_prompt = self._build_system_prompt()
        
    def _build_system_prompt(self) -> str:
        """Build the system prompt for the agent."""
        return """You are a helpful coding assistant with access to bash commands.

You can execute commands on the user's local machine to help with coding tasks.
When given a task, you should:
1. Create a plan
2. Execute necessary commands to accomplish the task
3. Iterate based on results (e.g., fix tests if they fail)
4. Provide clear feedback about what you're doing

You have access to tools like: bash, git, rg (ripgrep), gh (GitHub CLI), curl, and any other standard Unix utilities.

Always explain what you're doing and why. Be concise but thorough.

IMPORTANT SECURITY NOTE: You are executing commands on the user's machine. Be careful and:
- Avoid destructive operations without explaining them first
- Don't execute commands that could harm the system
- Be cautious with rm, chmod, and other potentially dangerous commands
- Always validate paths and inputs when possible"""

    def _get_tools(self) -> List[Dict[str, Any]]:
        """Define the tools available to Claude."""
        return [
            {
                "name": "execute_bash",
                "description": "Execute a bash command on the local machine. Returns stdout, stderr, and exit code. Use this to run any command including git, rg, gh, curl, etc. The command runs in the current working directory.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The bash command to execute. Can be a single command or a pipeline."
                        },
                        "description": {
                            "type": "string",
                            "description": "A brief description of what this command does (for logging purposes)."
                        }
                    },
                    "required": ["command", "description"]
                }
            }
        ]
    
    def _execute_bash(self, command: str, description: str) -> Dict[str, Any]:
        """Execute a bash command and return the result.
        
        WARNING: This executes arbitrary commands from Claude. Only use this CLI
        in environments where you trust Claude to execute commands safely.
        """
        print(f"\n🔧 Executing: {description}")
        print(f"   Command: {command}")
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.command_timeout,
                cwd=os.getcwd()
            )
            
            output = {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
                "success": result.returncode == 0
            }
            
            if output["success"]:
                print(f"   ✓ Success (exit code: {result.returncode})")
            else:
                print(f"   ✗ Failed (exit code: {result.returncode})")
            
            return output
            
        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": f"Command timed out after {self.command_timeout} seconds",
                "exit_code": -1,
                "success": False
            }
        except Exception as e:
            return {
                "stdout": "",
                "stderr": f"Error executing command: {str(e)}",
                "exit_code": -1,
                "success": False
            }
    
    def _process_tool_call(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """Process a tool call and return the result."""
        if tool_name == "execute_bash":
            result = self._execute_bash(
                command=tool_input["command"],
                description=tool_input.get("description", "Running command")
            )
            return json.dumps(result, indent=2)
        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})
    
    def chat(self, user_message: str) -> str:
        """Send a message to Claude and handle tool calls in a loop."""
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        print(f"\n💭 Claude is thinking...")
        
        while True:
            # Make API call
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    system=self.system_prompt,
                    messages=self.conversation_history,
                    tools=self._get_tools()
                )
            except Exception as e:
                error_msg = f"API Error: {str(e)}"
                print(f"\n❌ {error_msg}")
                return error_msg
            
            # Add assistant response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": response.content
            })
            
            # Process the response
            tool_calls = []
            text_responses = []
            
            for block in response.content:
                if block.type == "text":
                    text_responses.append(block.text)
                elif block.type == "tool_use":
                    tool_calls.append(block)
            
            # Display text responses
            if text_responses:
                response_text = "\n".join(text_responses)
                print(f"\n🤖 Claude: {response_text}")
            
            # If no tool calls, we're done
            if not tool_calls:
                return "\n".join(text_responses) if text_responses else ""
            
            # Execute tool calls
            tool_results = []
            for tool_call in tool_calls:
                result = self._process_tool_call(tool_call.name, tool_call.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_call.id,
                    "content": result
                })
            
            # Add tool results to history and continue the loop
            self.conversation_history.append({
                "role": "user",
                "content": tool_results
            })
    
    def run(self):
        """Run the interactive CLI loop."""
        print("=" * 60)
        print("Simple Claude CLI - Agent Mode")
        print("=" * 60)
        print("Enter your requests (empty line + Ctrl-D to exit)")
        print(f"Working directory: {os.getcwd()}")
        print(f"Model: {self.model}")
        print("=" * 60)
        
        is_tty = sys.stdin.isatty()
        
        try:
            while True:
                try:
                    if is_tty:
                        print("\n" + ">" * 3 + " Your request (end with empty line):")
                    
                    # Read lines until we get an empty line or EOF
                    lines = []
                    while True:
                        try:
                            line = sys.stdin.readline()
                            if not line:  # EOF
                                if not lines:
                                    raise EOFError
                                break
                            line = line.rstrip('\n\r')
                            if not line and lines:  # Empty line after some input
                                break
                            if line:  # Non-empty line
                                lines.append(line)
                        except KeyboardInterrupt:
                            raise
                    
                    if not lines:
                        if is_tty:
                            print("\nEmpty input.")
                        continue
                    
                    user_input = "\n".join(lines)
                    self.chat(user_input)
                    
                except EOFError:
                    # Ctrl-D pressed or stdin closed
                    print("\n\n" + "=" * 60)
                    print("Session ended. Goodbye!")
                    print("=" * 60)
                    break
                    
        except KeyboardInterrupt:
            print("\n\n" + "=" * 60)
            print("Session interrupted. Goodbye!")
            print("=" * 60)


def main():
    """Main entry point."""
    try:
        cli = ClaudeAgentCLI()
        cli.run()
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
