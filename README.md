# simple-claude-cli

A simple command-line interface for Claude's Agent API with tool calling capabilities.

## Features

- **Interactive stdin-based CLI**: Enter requests interactively, Claude responds with plans and actions
- **Agentic behavior**: Claude can execute bash commands (git, rg, gh, curl, etc.) to accomplish tasks
- **Session-based**: One CLI invocation = one session with conversation history
- **Tool execution**: Claude autonomously runs commands and iterates based on results

## Security Warning

⚠️ **This CLI allows Claude to execute arbitrary bash commands on your machine.** Only use this in:
- Development environments where you trust Claude's decisions
- Sandboxed/containerized environments
- Systems where the potential impact of commands is limited

Claude is instructed to be careful, but you should:
- Review what Claude plans to do before confirming
- Monitor command execution
- Use in controlled environments
- Set appropriate timeouts

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

The CLI supports the following environment variables:
- `ANTHROPIC_API_KEY` (required): Your Anthropic API key
- Command timeout: Can be configured programmatically (default: 300 seconds)

Model selection: Uses `claude-3-7-sonnet-20250219` by default (supports tool calling)

## Usage

Set your Anthropic API key:
```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

Run the CLI:
```bash
python3 simple_claude_cli.py
```

Enter your requests at the prompt. You can enter multi-line requests - just press Enter twice (empty line) to submit. Claude will:
1. Create a plan for your task
2. Execute necessary commands (bash, git, tests, etc.)
3. Iterate and fix issues based on results
4. Provide feedback throughout

Press `Ctrl-D` on an empty line to end the session.

You can also pipe input:
```bash
echo "List all Python files" | python3 simple_claude_cli.py
```

## Example

```
>>> Your request: Create a Python function to calculate fibonacci numbers and test it

💭 Claude is thinking...

🤖 Claude: I'll create a fibonacci function with tests. Let me start by creating the module.

🔧 Executing: Create fibonacci.py
   Command: cat > fibonacci.py << 'EOF'
def fibonacci(n):
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]
    
    fib = [0, 1]
    for i in range(2, n):
        fib.append(fib[-1] + fib[-2])
    return fib
EOF
   ✓ Success (exit code: 0)

🔧 Executing: Create test file
   Command: cat > test_fibonacci.py << 'EOF'
import unittest
from fibonacci import fibonacci

class TestFibonacci(unittest.TestCase):
    def test_fibonacci(self):
        self.assertEqual(fibonacci(0), [])
        self.assertEqual(fibonacci(1), [0])
        self.assertEqual(fibonacci(5), [0, 1, 1, 2, 3])

if __name__ == '__main__':
    unittest.main()
EOF
   ✓ Success (exit code: 0)

🔧 Executing: Run tests
   Command: python3 test_fibonacci.py
   ✓ Success (exit code: 0)

🤖 Claude: Done! Created fibonacci.py with the function and test_fibonacci.py with tests. All tests pass.
```

## Requirements

- Python 3.7+
- `anthropic` Python package
- Anthropic API key
- Standard Unix tools (bash, git, rg, gh, curl, etc.) as needed

## License

MIT License - see LICENSE file