import sys
sys.stdout.reconfigure(line_buffering=True)

import json
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from lead_scraper.schemas import LeadInfo

llm = ChatOllama(model="qwen3:8b", base_url="http://localhost:11434", temperature=0.0, format="json")
parser = JsonOutputParser(pydantic_object=LeadInfo)
prompt = PromptTemplate(
    template="Extract lead info from text:\n\n{content}\n\nInstructions:\n{format_instructions}",
    input_variables=["content"],
    partial_variables={"format_instructions": parser.get_format_instructions()}
)

chain = prompt | llm | parser

print("Invoking chain...", flush=True)
res = chain.invoke({"content": "Acme Corp is located in San Francisco, CA. Email: info@acme.com, Phone: +1-555-0199, CEO: John Smith"})
print("Parsed result:", res, flush=True)
print("Type:", type(res), flush=True)
