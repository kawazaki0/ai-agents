import copy
import json

from openai import AzureOpenAI
import httpx
import anthropic


class AIAgent:
    def __init__(self, config, tools=None):
        pass

    def __call__(self, message: str) -> str:
        raise NotImplementedError(
            "Base AIAgent class does not implement any model. Use AIAgentAzure or AIAgentAnthropic.")

    def _execute(self) -> str:
        raise NotImplementedError(
            "Base AIAgent class does not implement any model. Use AIAgentAzure or AIAgentAnthropic.")


class AIAgentAzure(AIAgent):
    MODEL_NAME = "gpt-4o-2024-11-20"

    def __init__(self, config):
        super().__init__(config)
        self._open_ai_client = AzureOpenAI(
            api_key=config.azure_api_key,
            azure_endpoint=config.azure_endpoint,
            api_version=config.azure_api_version,
            http_client=httpx.Client(verify=False)
        )
        self._temperature = config.temperature
        self._agent_state = [
            {
                "role": "system",
                "content": config.system_prompt
            }
        ]

    def __call__(self, message: str) -> str:
        self._agent_state.append(
            {
                "role": "user", "content": message
            }
        )
        result = self._execute()
        self._agent_state.append(
            {
                "role": "assistant", "content": result
            }
        )
        return result

    def _execute(self) -> str:
        response = self._open_ai_client.chat.completions.create(
            model=self.MODEL_NAME,
            messages=self._agent_state,
            temperature=self._temperature
        )
        return response.choices[0].message.content


class AIAgentAnthropic(AIAgent):
    MODEL_NAME = "claude-sonnet-4-0"

    def __init__(self, config, available_tools):
        super().__init__(config)
        self.anthropic = anthropic.Anthropic(api_key=config.anthropic_api_key)
        self._temperature = config.temperature
        self.system_prompt = config.system_prompt
        self._agent_state = []
        self._available_tools = available_tools

    def __call__(self, message: str) -> str:
        self._agent_state.append(
            {
                "role": "user", "content": message
            }
        )
        result = self._execute()
        self._agent_state.append(
            {
                "role": "assistant", "content": result
            }
        )
        return result

    def _execute(self) -> str:
        tools_for_anthropic = [{"name": tool_key, "input_schema": tool["inputSchema"], "description": tool['description']} for tool_key, tool in self._available_tools.items()]  # ---

        anthropic_args = {
            "system": self.system_prompt,
            "model": self.MODEL_NAME,
            "max_tokens": 1000,
            "messages": self._agent_state,
            "tools": tools_for_anthropic,  # ---
        }
        anthropic_args_readable = copy.deepcopy(anthropic_args)
        if "api_key" in anthropic_args_readable:
            anthropic_args_readable["api_key"] = "****"
        anthropic_args_readable['system'] = (anthropic_args_readable['system'][:75] + '...') if len(anthropic_args_readable['system']) > 75 else anthropic_args_readable['system']
        print(f"[ANTHROPIC_CALL] {repr(anthropic_args_readable)}")
        response = self.anthropic.messages.create(**anthropic_args)
        response_readable = [f"{repr(c)}" for c in response.content]
        print(f"[ANTHROPIC_RESPONSE] {repr(response_readable)}")
        final_text = []
        for content in response.content:
            if content.type == 'text':
                final_text.append(content.text)
            if content.type == 'tool_use':  # ---
                final_text.append(content.name + ": " + json.dumps(content.input))  # ---

        return ''.join(final_text)
