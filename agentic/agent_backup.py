
from planner import plan_request
from validator import validate_request
from tools import list_files, read_file, summarize


def run_agent(command):
    request = plan_request(command)

    if request is None:
        return "Sorry, I don't understand that request."

    valid, message = validate_request(request)

    if not valid:
        return message

    tool = request["tool"]
    arguments = request["arguments"]

    try:
        if tool == "list_files":
            return list_files()

        elif tool == "read_file":
            return read_file(arguments["path"])

        elif tool == "summarize":
            text = arguments["text"]

            if text.endswith(".txt") or text.endswith(".md"):
                text = read_file(text)

            return summarize(text)

    except Exception as e:
        return "Error: " + str(e)


def main():
    print("Agentic AI System connected to xv6")
    print("Type 'exit' to quit")

    while True:
        command = input("\nYou: ")

        if command.lower() == "exit":
            break

        response = run_agent(command)
        print("Agent:", response)


if __name__ == "__main__":
    main()
