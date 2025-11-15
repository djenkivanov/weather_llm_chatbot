# LLM Chatbot with tools
LLM Chatbot created using OpenAI's `davinci-002` document completion LLM with tool assistance capabilities.

```
You: What's the meaning of life?
Assistant: Let me check that for you.
$TOOL:what_is_the_meaning_of_life$
```
**If only it were that easy davinci...** 

Existential crises aside,
this chatbot can call tools to help with things, such as weather.
Here's a simple conversation with the weather tool.
```
Assistant ready. Type your message. Type /quit to exit.

You: Hello, what can you help me with?
Assistant: I can help you with anything you need.

You: Okay, can you tell me the weather in Gent?
Assistant: The current weather in Gent is 30 degrees Celsius, sunny, clear skies.

You: What about Geneva?
Assistant: The current weather in Geneva is 22 degrees Celsius, partly cloudy.

You: Thanks! And can you give me the weather for San Francisco?
Assistant: The current weather in San Francisco is 18 degrees Celsius, foggy.

You: Perfect, thank you!
Assistant: You're welcome.
```

This is what the process flowchart looks like.
![LLM Workflow](/img/llm_workflow.png)

This is a prototpe with a hardcoded `get_weather` tool, but can easily be replaced with a real API call.