from llm_planner import plan_with_llm
from validator import validate_request
from tools import list_files, read_file, summarize


def run_request(user_input):
    request = plan_with_llm(user_input)

    if request is None:
        return "LLM could not generate a valid tool call."

    print("\nLLM proposed:", request)

    valid, message = validate_request(request)

    if not valid:
        return "Request rejected: " + message

    print("Validator:", message)

    tool = request["tool"]
    args = request["arguments"]

    if tool == "list_files":
        return list_files()

    elif tool == "read_file":
        return read_file(args["path"])

    elif tool == "summarize":
        return summarize(args["text"])

    return "Tool not supported"


if __name__ == "__main__":
    result = run_request("Show me the files available in xv6.")
    print("\nAgent result:")
    print(result)
