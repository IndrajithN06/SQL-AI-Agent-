from app.llm import llm

response = llm.invoke("Explain what a SQL JOIN is in one sentence.")

print(response.content)
