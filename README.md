# Cloudflare LLM API Wrapper
A Python wrapper for the Cloudflare Workers AI API

## Features:
- Text prompts and responses
- Conversation history
- Access to history to manage previous messages
- Tool definition, usage, and execution

## To Do:
- Add to PyPI
- Add tool usage

## Getting Started:
> Note that since the project is not yet on PyPI, it cannot be installed via `pip install ...`, and the following method (also easy) must be used.
1. Download the `LLM_API.py` file and place it in your working directory.
2. Add `from LLM_API import *` to the top of your Python script
3. Initialize an `LLM_Convo` object with your chosen model, account number, API key, and optional tools (an `LLM_Tools` object). The first 3 pieces of info can be found on the Cloudflare website.
4. Optionally call `set_system_message` from your `LLM_Convo` object to set a system message to instruct the LLM.
5. Call `send_user_message` from your `LLM_Convo` object to prompt the LLM, and access the function's return value for its response.
6. See docs below for further usage details, or check out the [example](https://github.com/FinnE145/Cloudflare-LLM-API-Wrapper/blob/main/example.py)

# Docs:
### LLM_Convo
**`LLM_Convo()`** [Constructor]\
*Parameters*:
- **`model_name`**:`str` - The model name to be used in the API URL. Should look something like `@cf/meta/llama-3.3-70b-instruct-fp8-fast`
- **`account_id`**:`str` - Your account ID from the Cloudflare Workers dashboard.
- **`api_token`**:`str` - An API token from your Cloudflare account settings.
- **`tools`**:`LLM_Tools` - [*Optional*] An `LLM_Tools` object containing tool definitions to pass to the LLM, to be used and executed.

**`.set_system_message()`**\
*Parameters*:
- **`message`**:`str` - A system message to be given to the LLM (usually has instructions)

**`.send_user_message()`**\
*Parameters*:
- **`message`**:`str` - The prompt from the user to be given to the LLM (tools will be included)
- **`debug`**:`str` - [*Optional* - Default `False`] Prints info for debugging responses\
*Returns*:
- `str` - The LLM's response. Any tools will be run before return, and the LLM is re-prompted for a response after a tool call. The return message and tool responses can also be accessed from `LLM_Convo.messages`

**`.model_name`**:`str` - The model name given to the constructor\
**`.account_id`**:`str` - The account ID given to the constructor\
**`.api_token`**:`str` - The API token given to the constructor\
**`.tools`**:`LLM_Tools` - The tools given to the constructor\
**`.messages`**:`LLM_Messages` - A collection of message objects that represent system, tool, assistant, and user messages\
**`.API`**:`LLM_API` - The API object used to make requests, manage tool calls, etc\

### LLM_Tools
**`LLM_Tools`** [Constructor]\
*Parameters*:
- **`tools`**:`dict[str, tuple[Callable, dict]]` - A dictionary with keys being the tool name, and values being a tuple of the function to call for that tool, and the tool API structure as given by the Cloudflare docs (option 1)

**`.get_function()`**\
*Parameters*:
- **`name`**:`str` - The tool name\
*Returns*:
- `Callable` - The function assigned to that tool

**`.get_api_structure()`**\
*Parameters*:
- **`name`**:`str` - The tool name\
*Returns*:
- `dict` - The API structure assigned to the tool

**`.to_list()`**\
*Returns*:
- `list[dict]` - A list of dictionaries in LLM structure format

Individual tools' functions can be accessed by name as attributes. Their structures can be obtained by accessing the attribute found by appending `_struct` to the tool name.

The other classes contained in the module do not commonly need to be accessed, but their methods and properties are relatively self-explanatory. Feel free to read the source code for them or ask as an issue in this repo.
