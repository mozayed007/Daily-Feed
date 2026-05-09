from pydantic_ai import Agent
import inspect

sig = inspect.signature(Agent.__init__)
print("Agent.__init__ params:")
for name, param in sig.parameters.items():
    default = param.default
    if default is inspect.Parameter.empty:
        print(f"  {name}: <required>")
    else:
        print(f"  {name}: {default}")

# Try to create one
try:
    from pydantic_ai_litellm import LiteLLMModel
    m = LiteLLMModel(model_name="openai/gpt-4o")
    a = Agent(model=m, system_prompt="hi", result_type=None)
    print("OK: Agent created with result_type")
except Exception as e:
    print(f"FAIL: {e}")
