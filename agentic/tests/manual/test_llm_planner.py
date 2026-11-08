from llm_planner import plan_with_llm

request = plan_with_llm("Show me the files available in xv6.")

print("LLM proposed request:")
print(request)
