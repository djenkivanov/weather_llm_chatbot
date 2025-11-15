import json
import re
import os
from dotenv import load_dotenv
from typing import Dict, List, Tuple, Callable, Any
from openai import OpenAI

load_dotenv()

SYSTEM_PROMPT = """
You are Assistant: helpful, concise, friendly.
You respond in a back-and-forth dialogue with the User.

You can call TOOLS by writing a new line that is wrapped in a dollar sign:

$TOOL:<tool_name> <json_arguments>$

After a tool call, end your response and wait for the tool's result (it will appear in the Transcript next as Tool:<name>),
then continue with a normal Assistant message that uses the tool result.
Only use tool results when they've been provided in the Transcript, do not invent them.
Only call tools when clearly useful.

Example Transcript with a tool call for the weather:
User: What's the weather like in Lausanne?
Assistant: Let me check the weather for you.

$TOOL:get_weather {"city": "Lausanne"}$

Tool:get_weather: {"temp_c": 14, "condition": "rainy and cloudy"}

Assistant: The current weather in Lausanne is 14 degrees Celsius, rainy and cloudy.
<END>
User:

Remember to be concise and friendly in your responses.
"""


# hardcoded sample, can be replaced with a real weather API call
def get_weather(city: str) -> Dict[str, Any]:
    """
    Returns a sample weather report for the given city.
    """
    sample = {
        "Gent": {"temp_c": 30, "condition": "sunny, clear skies"},
        "Geneva": {"temp_c": 22, "condition": "partly cloudy"},
        "San Francisco": {"temp_c": 18, "condition": "foggy"},
    }
    # print(f"===== Getting weather for city: {city}")
    return sample.get(city)


TOOLS: Dict[str, Callable[..., Any]] = {
    "get_weather": get_weather,
}

TOOL_INV = [
    {"name": "get_weather", "args": {"city": "str"}, "returns": {"temp_c": "int", "condition": "str"},
     "desc": "Returns current weather for a specific city."},
]


def generate_tools_inv() -> str:
    all_tools = ["TOOLS AVAILABLE:"]
    for t in TOOL_INV:
        all_tools.append(
            f"- {t['name']}({', '.join([k+': '+v for k, v in t['args'].items()])})"
            f" -> {json.dumps(t['returns'])}: {t['desc']}"
        )
    return "\n".join(all_tools)


def generate_prompt(transcript: List[Tuple[str, str]]) -> str:
    """
    Generates the full prompt including system prompt, tool inv, and transcript.
    """
    msgs = [SYSTEM_PROMPT, generate_tools_inv(), "\n\n", "Transcript:"]
    for role, content in transcript:
        msgs.append(f"{role}: {content}".rstrip()) # dont use strip to preserve formatting, rstrip safer
    msgs.append("Assistant:")
    return "\n".join(msgs)


client = OpenAI(api_key=os.getenv("OPENAI_KEY"))


def complete(prompt: str) -> str:
    """
    Calls completion model 'davinci-002' with the given prompt and returns the response.
    """
    # https://platform.openai.com/docs/api-reference/completions
    response = client.completions.create(
        model="davinci-002",
        prompt=prompt,
        max_tokens=300,
        temperature=0.4,
        stop=["<END>", "User:", "Tool:"],
    )
    return response.choices[0].text


TOOL_CALL_REGEX = re.compile(r"^\$TOOL:(\w+)\s({.*})\$$", re.MULTILINE)


def detect_tool_call(text: str):
    """
    Returns (tool_name, args_dict) or None.
    """
    tools = TOOL_CALL_REGEX.search(text.strip())
    if not tools:
        return None
    tool_name = tools.group(1)
    try:
        args = json.loads(tools.group(2))
    except json.JSONDecodeError:
        return None
    return tool_name, args


def chat_loop():
    transcript: List[Tuple[str, str]] = []
    print("Assistant ready. Type your message. Type /quit to exit.")
    while True:
        user_msg = input("You: ").rstrip()
        if user_msg == "/quit":
            break
        transcript.append(("User", user_msg))

        for _ in range(5): # max 5 tool calls per user message
            prompt = generate_prompt(transcript)
            # print(f'--- Prompt ---\n{prompt}\n--- End Prompt ---')
            completion = complete(prompt).rstrip()
            # print(f'--- Completion ---\n{completion}\n--- End Completion ---')
            called_tool = detect_tool_call(completion)
            # print(called_tool)
            if called_tool:
                tool_name, tool_args = called_tool
                if tool_name not in TOOLS:
                    transcript.append(("Assistant", f"(Tried unknown tool {tool_name}.)"))
                    break
                try:
                    result = TOOLS[tool_name](**tool_args)
                    # print(f'--- Tool Result ---\n{result}\n--- End Tool Result ---')
                except Exception as e:
                    transcript.append(("Assistant", f"(Tool call error: {e})"))
                    break

                transcript.append(("Assistant", f"$TOOL:{tool_name} {json.dumps(tool_args)}$"))
                transcript.append((f"Tool:{tool_name}", json.dumps(result)))
                continue
            else:
                transcript.append(("Assistant", completion))
                print(f"Assistant: {completion}")
                break
        else:
            transcript.append(("Assistant", "(Stopped after too many tool steps.)"))
            print("Assistant: (Stopped after too many tool steps.)")

if __name__ == "__main__":
    chat_loop()
