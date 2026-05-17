from agentease import AgentEase


client = AgentEase(api_key="your-provider-api-key", provider="openai", model="gpt-4o-mini")

result = client.triage.run(
    "Customer jane@example.com says they were charged twice and wants a refund."
)

print(result.model_dump())
