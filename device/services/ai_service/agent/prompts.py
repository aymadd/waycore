"""Prompt templates for agentic AI tool use."""

from __future__ import annotations

from typing import Any

# Template for describing tools to the LLM
TOOL_DESCRIPTION_TEMPLATE = """
## Available Tools

You have access to the following tools. To use a tool, respond with a JSON object:

```json
{{"tool": "tool_name", "arguments": {{"arg1": "value1", "arg2": "value2"}}}}
```

### Tools:
{tools_list}

### Important:
- Only use tools when necessary to answer the user's question
- Always wait for tool results before providing your final answer
- If a tool fails, explain the issue and try an alternative approach
- Never fabricate tool results - only use actual data returned
"""

# Template for each tool in the list
TOOL_ENTRY_TEMPLATE = """
**{name}**: {description}
  Parameters: {parameters}
"""


def format_tool_list(tools: list[dict[str, Any]]) -> str:
    """Format a list of tools for inclusion in the system prompt.

    Args:
        tools: List of tool definitions with name, description, parameters.

    Returns:
        Formatted string describing all tools.
    """
    if not tools:
        return "No tools available."

    entries = []
    for tool in tools:
        params = tool.get("parameters", {}).get("properties", {})
        param_str = ", ".join(params.keys()) if params else "none"

        entries.append(
            TOOL_ENTRY_TEMPLATE.format(
                name=tool["name"],
                description=tool.get("description", "No description"),
                parameters=param_str,
            )
        )

    return "\n".join(entries)


def get_tool_system_prompt(tools: list[dict[str, Any]]) -> str:
    """Generate the system prompt section for tool use.

    Args:
        tools: List of tool definitions.

    Returns:
        System prompt section describing available tools.
    """
    tools_list = format_tool_list(tools)
    return TOOL_DESCRIPTION_TEMPLATE.format(tools_list=tools_list)


# Template for formatting tool results
TOOL_RESULT_TEMPLATE = """
Tool Result [{tool_name}]:
{result}
"""


def format_tool_result(tool_name: str, result: Any, error: str | None = None) -> str:
    """Format a tool result for inclusion in the conversation.

    Args:
        tool_name: Name of the tool that was called.
        result: The result from the tool.
        error: Error message if the tool failed.

    Returns:
        Formatted tool result string.
    """
    if error:
        return f"Tool Error [{tool_name}]: {error}"

    if isinstance(result, list):
        # MCP tools return list of content objects
        texts = []
        for item in result:
            if hasattr(item, "text"):
                texts.append(item.text)
            elif isinstance(item, dict) and "text" in item:
                texts.append(item["text"])
            else:
                texts.append(str(item))
        result_str = "\n".join(texts)
    else:
        result_str = str(result)

    return TOOL_RESULT_TEMPLATE.format(tool_name=tool_name, result=result_str)


# Confirmation prompt for dangerous tools
CONFIRMATION_PROMPT = """
I need your permission to execute the following action:

**Tool**: {tool_name}
**Arguments**: {arguments}

{warning}

Do you want me to proceed?
"""


def get_confirmation_prompt(
    tool_name: str,
    arguments: dict[str, Any],
    warning: str = "",
) -> str:
    """Generate a confirmation prompt for dangerous tools.

    Args:
        tool_name: Name of the tool.
        arguments: Tool arguments.
        warning: Optional warning message.

    Returns:
        Confirmation prompt string.
    """
    import json

    args_str = json.dumps(arguments, indent=2)
    return CONFIRMATION_PROMPT.format(
        tool_name=tool_name,
        arguments=args_str,
        warning=warning or "This action may have side effects.",
    )
