from pathway.xpacks.llm import llms
import os

hf_api_token = os.getenv("HF_API_TOKEN")

llm = llms.LiteLLMChat(
    model="falcon-7b-instruct",
    provider="huggingface",
    device="cpu",
    batch_size=1,
    api_key=hf_api_token
)

response = llm([{"role": "user", "content": "Hello world"}])
print(response)