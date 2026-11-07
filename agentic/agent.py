from planner import plan_request
from validator import validate_request
from tools import list_files, read_file, summarize, get_safe_path


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
            return str(list_files())

        elif tool == "read_file":
            return read_file(arguments["path"])

        elif tool == "summarize":
            text = arguments["text"]

            try:
                file_path = get_safe_path(text)

                if file_path.is_file():
                    text = read_file(text)

            except (ValueError, FileNotFoundError):
                pass

            return summarize(text)

    except (ValueError, FileNotFoundError, OSError) as e:
        return str(e)


def main():

    print("Agentic AI System")
    print("Type 'exit' to quit")

    while True:
        command = input("\nYou: ")

        if command.lower() == "exit":
            break

        response = run_agent(command)
        print("Agent:", response)


if __name__ == "__main__":
    main()
