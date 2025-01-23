import requests
from typing_extensions import Type
from collections.abc import Callable
from iformat import iprint

class LLM_Tools:
    def __init__(self, tools:dict[str, tuple[Callable, dict]]=None) -> None:
        self._tools = tools or {}

    def get_function(self, name:str) -> Callable:
        return self._tools[name][0]

    def get_api_structure(self, name:str) -> dict:
        return self._tools[name][1]

    def add_tool(self, name:str, function:Callable, api_structure:dict) -> None:
        self._tools[name] = (function, api_structure)

    def to_list(self) -> list[dict]:
        return [
            {
                "name": name,
                "description": api_structure["description"],
                "parameters": api_structure["parameters"],
                "returns": api_structure.get("returns", {})
            }
            for name, (function, api_structure) in self._tools.items()
        ]
    
    def __setattr__(self, name:str, value) -> None:
        if name=="_tools":
            super().__setattr__(name, value)
        elif isinstance(value, tuple):
            self.add_tool(name, *value)
        elif isinstance(value, Callable):
            self.add_tool(name, value, {})
        elif isinstance(value, dict):
            self.add_tool(name.removesuffix("_struct"), lambda: None, value)
        else:
            super().__setattr__(name, value)

    def __getattr__(self, name) -> Callable|dict:
        if name in self._tools:
            return self.get_function(name)
        if name.removesuffix("_struct") in self._tools:
            return self.get_api_structure(name.removesuffix("_struct"))

class LLM_Message:
    def __init__(self, role:str, content:str="", name:str=None) -> None:
        self.role = role
        self.content = content
        self.tool_name = name
    
    def to_dict(self) -> dict:
        d = {
            "role": self.role,
            "content": self.content
        }
        d.update(name=self.tool_name) if self.tool_name else None
        return d
    
    def user(content:str) -> Type["LLM_Message"]:
        return LLM_Message("user", content)
    
    def assistant(content:str) -> Type["LLM_Message"]:
        return LLM_Message("assistant", content)
    
    def tool(name:str, content:str="") -> Type["LLM_Message"]:
        return LLM_Message("tool", content, name)
    
    def __str__(self) -> str:
        return self.content
    

class LLM_Messages:
    def __init__(self, messages:list[LLM_Message]=None) -> None:
        self.messages = messages or []

    def __getitem__(self, index:int) -> LLM_Message:
        return self.messages[index]
    
    def __setitem__(self, index:int, value:LLM_Message) -> None:
        self.messages[index] = value

    def create(role:str, content:str) -> Type["LLM_Messages"]:
        return LLM_Messages([LLM_Message(role, content)])

    def append(self, message:LLM_Message) -> None:
        self.messages.append(message)

    def extend(self, messages:Type["LLM_Messages"]) -> None:
        self.messages.extend(messages.messages)
    
    def add_message(self, role:str, content:str) -> None:
        self.messages.append(LLM_Message(role, content))
    
    def to_list(self) -> list[dict]:
        return [message.to_dict() for message in self.messages]
    
    def remove_system_messages(self) -> None:
        self.messages = [message for message in self.messages if message.role != "system"]

    def without_system_messages(self) -> Type["LLM_Messages"]:
        return LLM_Messages([message for message in self.messages if message.role != "system"])
    
    def last_message(self) -> LLM_Message:
        return self.messages[-1]
    
    def last_response(self) -> str:
        return str(self.messages[-1]) if self.messages[-1].role == "assistant" else str(self.messages[-2])
    
    def last_input(self) -> str:
        return str(self.messages[-1]) if self.messages[-1].role == "user" else str(self.messages[-2])
    
    def last_tool_calls(self) -> list[dict]:
        tool_call_messages = []
        for message in self.messages:
            if message.role == "tool":
                tool_call_messages.append(message)
            else:
                break
        return tool_call_messages

class LLM_Output:
        def __init__(self, result:dict, all_tools:LLM_Tools=None) -> None:
            self.result = result
            self.response = result["response"]
            self.tool_calls = result.get("tool_calls", [])
            self.all_tools = all_tools

        def _check_tool_call(self, tool_call:dict) -> bool:
            #print("Checking tool call:", tool_call)
            if tool_call["name"] not in self.all_tools._tools:
                print(f"LLM tried calling nonexistant tool '{tool_call['name']}'")
                return False
            for arg_name in tool_call["arguments"].keys():
                if arg_name not in self.all_tools.get_api_structure(tool_call["name"])["parameters"]["properties"]:
                    print(f"LLM tried calling '{tool_call['name']}' with nonexistant argument '{arg_name}'")
                    return False
            if len(tool_call["arguments"]) != len(self.all_tools.get_api_structure(tool_call["name"])["parameters"]["properties"]):
                print(f"LLM tried calling '{tool_call['name']}' with incorrect number of arguments")
                return False
            return True

        def _cast_tool_arguments(self, tool_call:dict) -> dict:
            types = {
                "string": str,
                "integer": int,
                "boolean": bool,
                "object": dict,
                "array": list,
                "float": float,
                "decimal": float,
                "null": None
            }

            tool_name = tool_call["name"]
            arguments = tool_call["arguments"]
            for arg_name, arg_value in arguments.items():
                arg_type = self.all_tools.get_api_structure(tool_name)["parameters"]["properties"][arg_name]["type"]
                if arg_type.lower() in ["null", "none"]:
                    arguments[arg_name] = None
                else:
                    arguments[arg_name] = types[arg_type](arg_value)

        def _run_tools(self) -> LLM_Messages:
            tool_messages = LLM_Messages()
            for tool_call in self.tool_calls:
                tool_name = tool_call["name"]

                if not self._check_tool_call(tool_call):
                    tool_messages.append(
                        LLM_Message.tool(tool_name, "Tool Call Error: Either the tool does not exist or the arguments are incorrect.")
                    )
                    break
                self._cast_tool_arguments(tool_call)

                tool_func = self.all_tools.get_function(tool_name)
                tool_args = tool_call["arguments"]
                print(f"LLM called {tool_name}({', '.join(f'{k}={v}' for k, v in tool_args.items())})", end="")

                tool_res = tool_func(**tool_args)
                print(f" --> {tool_res}")

                tool_messages.append(
                    LLM_Message.tool(
                        tool_name,
                        str(tool_res)
                    )
                )
            #iprint("Tool messages:", tool_messages)
            return tool_messages
        
        def resolve_messages(self) -> LLM_Messages:
            return LLM_Messages.create("assistant", self.response) if self.response else self._run_tools()

class LLM_API:
    def __init__(self, model_name:str, account_id:str, api_token:str, tools:LLM_Tools) -> None:
        self.model_name = model_name
        self._account_id = account_id
        self._api_token = api_token
        self.api_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model_name}"
        self._headers = {"Authorization": f"Bearer {api_token}"}
        self.tools = tools

    def make_request(self, messages:LLM_Messages, tools:LLM_Tools=None, debug=False) -> LLM_Output:
        #iprint(self.tools.to_list() if tools is None else tools.to_list())
        iprint(f"sending request with tools: {', '.join(tool.name for tool in self.tools)}") if debug else ...
        res = requests.post(
            self.api_url,
            headers = self._headers,
            json = {
                "messages": messages.to_list(),
                "tools": self.tools.to_list() if tools is None else tools.to_list()
            }
        ).json()
        iprint(res) if debug else ...
        if res["success"]:
            return LLM_Output(res["result"], self.tools)
        elif res["errors"]:
            raise Exception(res["errors"][0]["message"])
        else:
            raise Exception("An unknown error occurred")

class LLM_Convo:
    def __init__(self, model_name:str, account_id:str, api_token:str, tools:LLM_Tools) -> None:
        self.model_name = model_name
        self.account_id = account_id
        self.api_token = api_token
        self.tools = tools
        self.API = LLM_API(model_name, account_id, api_token, tools)
        self.messages = LLM_Messages()

    def set_system_message(self, message:str) -> None:
        self.messages.add_message("system", message)

    def send_user_message(self, message:str, debug=False) -> str:
        self.messages.add_message("user", message)
        iprint("Original messages:", self.messages.to_list()) if debug else ...
        new_messages = self.API.make_request(self.messages, debug=debug).resolve_messages().without_system_messages()
        iprint("New messages:", new_messages.to_list()) if debug else ...
        self.messages.extend(new_messages)
        while new_messages.last_message().role == "tool":
            print("Last response was a tool, rerunning...") if debug else ...
            new_messages = self.API.make_request(self.messages, debug=debug).resolve_messages().without_system_messages()
            iprint("New messages:", new_messages.to_list()) if debug else ...
            self.messages.extend(new_messages)
        return self.messages.last_response()