from agent import AIAgent, AIAgentAzure, AIAgentAnthropic
from agent_tools import AgentTools
from utils import AIAgentConfig, ActionParser
import json


def tools_markdown(mcp_tools_dict):
    lines = ["\n## MCP Server Tools\n"]
    for name, info in mcp_tools_dict.items():
        lines.append(f"### `{name}`")
        if info.get("description"):
            lines.append(f"{info['description']}")
        schema = info.get("inputSchema", {})
        if schema:
            lines.append("**Input schema:**")
            lines.append("```json")
            lines.append(json.dumps(schema, indent=2))
            lines.append("```")
        lines.append("")
    return '\n'.join(lines)


def run_agent_loop(
        prompt: str,
        ai_agent: AIAgent,
        ai_agent_tools: AgentTools,
        action_parser: ActionParser,
        max_turns=5
):
    try:
        for _ in range(max_turns):
            # print(f"\n[SYSTEM] Input: {prompt}")
            result = ai_agent(prompt)
            for i, line in enumerate(result.split('\n')):
                if line.strip():
                    print(f"[ASSISTANT(line {i})] {line.strip()}")
            action, action_input = action_parser(result)
            if not action:
                break

            print(f"[SYSTEM] Action: {action}, Input: {action_input}")
            ai_tool = ai_agent_tools.get_tool(action.lower().strip())
            if ai_tool:
                action_result = ai_tool(action_input.strip())
                print(f"[SYSTEM] Tool result: {action_result}")
            else:
                available_tools = ai_agent_tools.get_available_tools().keys()
                action_result = f'Unknown tool "{action}". Available tools: {available_tools}'
                print(f"[SYSTEM] {action_result}")

            prompt = f"Observation: {action_result}"
    finally:
        ai_agent_tools.cleanup()


if __name__ == '__main__':
    config = AIAgentConfig.load_from_local(prompt_name_file="system_mcp.md")
    tools = AgentTools(config=config)
    tools.init()
    llm_tools = {}
    if config.use_llm_tools:
        llm_tools = tools.get_available_tools()
    else:
        config.system_prompt = config.system_prompt.replace("{{mcp_tools}}", tools_markdown(tools.get_available_tools()))

    run_agent_loop(
        prompt=input("[USER]: "),
        ai_agent=AIAgentAnthropic(config=config, available_tools=llm_tools),
        ai_agent_tools=tools,
        action_parser=ActionParser()
    )
