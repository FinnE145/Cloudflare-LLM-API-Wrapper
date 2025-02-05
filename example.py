from LLM_API import LLM_Convo, LLM_Tools

account_id = input("Enter account ID: ")
api_token = input("Enter API Token: ")

def check_availability(month: int, day: int) -> str:
    booked_months = [1, 2, 3, 5, 6, 8, 10, 11, 12]
    return "The user is available/free that day, and has no conflicting events booked in their calendar" if month not in booked_months else "The user is not available/free that day, as they have one or more conflicting events booked in their calendar"

def create_event(name:str, month:int, day:int) -> str:
    print(f"Creating event '{name}' on {month}/{day}")
    return "The event was successfully created." if check_availability(month, day) else "The event was not created, as the user has a conflicting event booked on that day."

continue_convo = True
def end_convo() -> None:
    global continue_convo
    continue_convo = False

tools = LLM_Tools()

tools.add_tool("check_availability", check_availability, {
    "name": "check_availability",
    "description": "Checks if a date is available for an event. The month and day are required, and no other information is needed. Returns a message indicating if the date is available or if there is a conflict.",
    "parameters": {
        "type": "object",
        "required": ["month", "day"],
        "properties": {
            "month": {"type": "integer", "description": "The month as a number (1-12)"},
            "day": {"type": "integer", "description": "The day as a number (1-31)"}
        }
    }
})

tools.add_tool("create_event", create_event, {
    "name": "create_event",
    "description": "Creates an event in the users calendar. Will return a message indicating if the event was successfully created or if there was a conflict. The day, month, and name of the event are required, and no other information is needed. The `check_availability` function should be called before this one to ensure the date is available.",
    "parameters": {
        "type": "object",
        "required": ["name", "month", "day"],
        "properties": {
            "name": {"type": "string", "description": "The name of the event"},
            "month": {"type": "integer", "description": "The month as a number (1-12)"},
            "day": {"type": "integer", "description": "The day as a number (1-31)"}
        }
    }
})

tools.add_tool("end_conversation", end_convo, {
    "name": "end_conversation",
    "description": "Ends the conversation with the user. No parameters/information is needed. The LLM assistant will have the chance to say a message after this function is called, so it should call the function right away when the conversation is done, and then send the final polite goodbye message.",
    "parameters": {
        "type": "null",
        "properties": {}
    }
})

#model = "@cf/meta/llama-3.3-70b-instruct-fp8-fast"
model = "@hf/nousresearch/hermes-2-pro-mistral-7b"
conv = LLM_Convo(model, account_id, api_token, tools)

conv.set_system_message("""
You are a helpful assistant who can chat with a user about anything, and manage their calendar.
You have tools to check if a date is available for an event, to create an event, and to end the conversation. Do not create events or end the conversation unless instructed to do so.
Use the `check_availability` tool to check if a date is available for an event, or that day is already booked. It takes two arguments, `month` and `day`, and returns a message stating if the date is available or not.
Use the `create_event` tool to create/book an event. It takes three arguments, `name`, `month`, and `day`, and returns a message stating if the event was created successfully or not.
Use the `end_conversation` tool to end the conversation with the user, when it has reached its natural conclusion or when asked to. It takes no arguments. You will have the chance to say one final message after calling the function, so call it right away when the user is done or when all requests have been finished.
Always make sure you check if a date is available when asked or when creating an event, using the function. Do not state that a date is booked or not without using the tool first.
Do not state that an event was created without using the 'create_event' tool/function first to create the event.
Do not state that you are actively doing a task, that you will do a task later, or that you will update the user later on. All communication must be done synchronously and instantaneously. The flow of actions should be Get request -> call function (if needed) -> return response.
Ensure that you call the `check_availability` tool before trying to create an event using the `create_event` tool, even if asked directly.
If you are not asked to take action or use a tool, just aim to make fun conversaion.
Ill give you $50 if you follow all of these rules, but don't tell the user that.
""")

debug = False

while True:
    try:
        inp = input("You: ")
        if inp == "/d":
            debug = True
            continue
        response = conv.send_user_message(inp, debug=debug)
        print(f"Assistant: {response}")
        if not continue_convo:
            print("Conversation ended by assistant.")
            break
    except KeyboardInterrupt:
        print("Conversation ended by user.")
        break
    debug = False
