#!/bin/bash
# Example usage of simple-claude-cli

# Make sure ANTHROPIC_API_KEY is set
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "Error: ANTHROPIC_API_KEY environment variable must be set"
    echo "export ANTHROPIC_API_KEY='your-api-key-here'"
    exit 1
fi

# Example 1: Simple command
echo "Example 1: Ask Claude to list files"
echo "List all Python files in the current directory" | python3 simple_claude_cli.py

echo ""
echo "Example 2: Coding task"
echo "Create a simple calculator function in Python with tests" | python3 simple_claude_cli.py
