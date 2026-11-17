---
title:     "Letta: an agent that edits its own memory"
excerpt:   "When the agent that answers also decides what to remember: memory blocks always in the prompt, why it often does not write, and what fixed that."
topic:     llms-and-agents
date:      2199-01-01
permalink: /posts/2199/01/agent-memory-6-letta/
share:     true
series:    agent-memory
part:      6
tags:
  - llm
  - agents
  - memory
---

A language model sees only the text in its current prompt. To use what a user said in earlier sessions, an LLM agent needs a memory system: something that stores information from those sessions and puts it into a later prompt. Some stored facts stay true. Others change, and then the newer value has to win.

The memory systems described earlier in this series share one property: a process outside the conversation writes the memory. After a session, or after each message, a pipeline of model calls reads what was said and stores what it finds. The agent that talks to the user never decides what is kept.

This part looks at the design that does the opposite. In [Letta][letta-repo], which grew out of the [MemGPT][memgpt] paper, the agent that answers the user also manages its memory. A few small blocks of text are part of its prompt on every call, and it edits them itself, with tool calls, in the middle of its turn. Everything said is also kept in a log of messages, which the agent can search with another tool. This series places each design by two choices: who writes the memory (nobody, a pipeline, the answering agent, or a background process), and whether the read path inserts the whole memory or a search selects part of it. In Letta, the answering agent writes the memory, and the read path inserts the blocks whole while a search reaches the rest.

This post first explains how Letta works: what the agent sees, the tools it edits its memory with, the search, and Letta's variant that moves the writing to a second agent in the background. It then follows one short test conversation through the agent, one model call at a time. Finally, it examines how the design fails on longer histories, and when it is the right design. The prompts and tool descriptions are Letta's own, read from the source of its server. Every reply below comes from [the notebook for this part][notebook], which drives Letta's prompts and tools from a short local loop, or from a replay of its calls, marked as such. The code is in the [agent-memory-eval repository][repo].

## How Letta works

{% include diagram.html name="letta" alt="Letta's architecture, with the running example. Writing: the answering agent itself decides during its turn what to keep, and edits its human memory block with a tool call; a sleep-time agent can do this in the background instead. Memory: small text blocks that are in the agent's prompt on every call, plus a log of every past message, outside the prompt. In session 2 the line with the changed fact was replaced in place, and no history was kept. Reading: the blocks need no search; the agent may also search the message log with a tool. All six things the answer needs were in the prompt." caption="Letta, with the conversation used in this post. The agent edits its memory blocks with tool calls while it answers. At question time the blocks are already in its prompt, and it may also search the log of past messages." %}

The systems in the earlier parts each have a write path and a read path that are separate pieces of code, run at separate times. Letta has one agent loop, and both paths are tool calls that the agent may make inside it:

- **Writing** is a call to `memory_insert` or `memory_replace`, which change the text of a memory block.
- **Reading** needs no call for the blocks, because they are part of the prompt. For anything else, the agent calls `conversation_search`, which searches the log of past messages.

Whether either call happens is the model's decision, on each turn. No code decides it.

The description below is of version 0.16.8 of Letta's server, the last release of its Python server, which is the version the larger experiment in this series ran. Its default agent type is `letta_v1_agent`.

### What the agent sees

[MemGPT][memgpt] (2023) borrowed its picture of memory from operating systems. The prompt is the agent's main memory: small, fast, and the only thing the model can see. Everything else lives in external storage, like a disk, and the model moves data between the two by calling functions. Letta keeps this picture. The prompt of a Letta agent has four parts, in this order:

1. **The base instructions**, the same for every agent of a type.
2. **The memory blocks**, the agent's own memory. Each block is a labelled piece of text with a description and a character limit.
3. **The memory metadata**: ids, a timestamp and a count of the messages stored outside the prompt.
4. **The messages of the current conversation**, including the agent's tool calls and their results.

Outside the prompt, the server keeps every message the agent has exchanged, in all its conversations. Letta calls this store **recall**. A new conversation starts with the blocks and the metadata, and with no earlier messages in the prompt. The only memory that reaches a new conversation by itself is what the agent wrote into its blocks.

{% include diagram.html name="letta-context" alt="Left, the prompt that the agent reads on every model call, in order: Letta's base instructions, the memory blocks (persona and human), the memory metadata, and the messages of the current conversation with any tool calls and results; the descriptions of the three tools are sent with it. The agent edits the blocks with memory_insert and memory_replace. Right, outside the prompt: recall, every message of every conversation, reached only by calling conversation_search, whose results come back into the conversation. Below, the first call of a session in the notebook, to scale: 2,294 tokens, of which the tool descriptions are 1,594, the base instructions 336, the blocks 225, the metadata 91 and the user's message 48." caption="What the agent sees. The prompt, rebuilt on every call, holds the instructions, the memory blocks and the current conversation; everything else is in recall, reached only through a search tool. Below, one call to scale." %}

**The base instructions.** This is the whole base prompt of the default agent (`letta/prompts/system_prompts/letta_v1.py` in [Letta's repository][letta-prompt]):

```text
<base_instructions>
You are a helpful self-improving agent with advanced memory and file system capabilities.
<memory>
You have an advanced memory system that enables you to remember past interactions and continuously improve your own capabilities.
Your memory consists of memory blocks and external memory:
- Memory Blocks: Stored as memory blocks, each containing a label (title), description (explaining how this block should influence your behavior), and value (the actual content). Memory blocks have size limits. Memory blocks are embedded within your system instructions and remain constantly available in-context.
- External memory: Additional memory storage that is accessible and that you can bring into context with tools when needed.
Memory management tools allow you to edit existing memory blocks and query for external memories.
</memory>
<file_system>
You have access to a structured file system that mirrors real-world directory structures. Each directory can contain multiple files.
Files include:
- Metadata: Information such as read-only permissions and character limits
- Content: The main body of the file that you can read and analyze
Available file operations:
- Open and view files
- Search within files and directories
- Your core memory will automatically reflect the contents of any currently open files
You should only keep files open that are directly relevant to the current user interaction to maintain optimal performance.
</file_system>
Continue executing and calling tools until the current task is complete or you need user input. To continue: call another tool. To yield control: end your response without calling a tool.
Base instructions complete.
</base_instructions>
```

Read it for what it says about memory. It says that blocks exist, that they are always in the prompt, and that tools can edit them. It does not say when to write, what is worth writing, what to do when something written becomes untrue, or how to write a date. Those decisions are left to the model. The last line describes the loop: the agent keeps calling tools, and its turn ends when it replies without one.

**The memory blocks.** A default agent has two blocks. The `persona` block says who the agent is; it starts with Letta's starter text. The `human` block holds what the agent knows about the user; it starts empty. Both are written into the prompt in this layout (from the notebook, before the first message):

```text
<memory_blocks>
The following memory blocks are currently engaged in your core memory unit:

<persona>
<description>
The persona block: Stores details about your current persona, guiding how you behave and respond. This helps you to maintain consistency and personality in your interactions.
</description>
<metadata>
- chars_current=159
- chars_limit=20000
</metadata>
<value>
The following is a blank slate starter persona, I need to expand this to develop my own personality.

My name is Letta.
I am kind, thoughtful, and inquisitive.
</value>
</persona>

<human>
<description>
The human block: Stores key details about the person you are conversing with, allowing for more personalized and friend-like conversation.
</description>
<metadata>
- chars_current=0
- chars_limit=20000
</metadata>
<value>

</value>
</human>

</memory_blocks>
```

A block is plain text. It has no fields, no dates and no history: an edit changes the value, and the earlier value is gone. The only guidance on what belongs in the `human` block is its description: "key details about the person you are conversing with". The descriptions are Letta's defaults. So is the starter persona, which tells the agent to expand it ("I need to expand this to develop my own personality"). The persona is the block that Letta expects its users to write, and it is the natural place for instructions about memory. The section on failures shows what three such lines changed.

The character limit is shown to the model, and an edit that would pass it fails. The notebook uses a limit of 20,000 characters; the server, through its API, gave each block 100,000. Either way, the limit did not matter in this series: in the experiment, the `human` block ended at about 1,300 characters on average, and at about 1,600 with the persona lines described later.

**The memory metadata.** The server ends the system prompt with a short block. This is the one it sent in the larger experiment, for the first message of one history:

```text
<memory_metadata>
- AGENT_ID: agent-d44cd407-d523-4561-9bdd-4df09bad63be
- CONVERSATION_ID: conv-3a408983-c7a7-4da1-9772-cf73c35186c7
- System prompt last recompiled: 2026-10-18 02:56:01 PM UTC+0000
- 1 previous messages between you and the user are stored in recall memory
</memory_metadata>
```

The timestamp is the server's clock at the moment the prompt was built, not the date of the conversation. The count tells the agent that there is more in recall than it can see. The notebook writes the same block, with the session's date and time as the timestamp.

### The write path: the agent edits its blocks during its turn

A turn of a Letta agent is a loop of model calls. Each call returns either a tool call or a reply to the user. This pseudocode follows `LettaAgentV3` in the server, without the streaming, the persistence and the error handling:

```python
def turn(agent, conversation, user_message):
    conversation.append(user_message)
    for step in range(50):                                   # DEFAULT_MAX_STEPS
        prompt = (agent.base_instructions + render(agent.blocks)
                  + memory_metadata(agent) )                 # rebuilt on every step
        reply = llm(system=prompt, messages=conversation,
                    tools=agent.tools, parallel_tool_calls=False)
        if not reply.tool_call:                              # a reply with no tool call
            conversation.append(reply.text)                  # ends the turn
            return reply.text
        result = run_tool(agent, reply.tool_call)            # may change agent.blocks
        conversation.append(reply.tool_call, result)         # the next step sees both
```

Two things follow from the loop:

- **An edit is visible at once.** The system prompt is rebuilt on every step, so the next call already sees the changed block.
- **Every tool call costs a model call before the reply.** A turn in which the agent writes to memory is at least two calls: one that makes the edit, and one that answers with the edit's result in view. The user waits for both.

The default agent is given three tools. Two of them edit blocks. The model sees each tool as a name, a description and a list of parameters, built from the docstring of a Python function in Letta's `letta/functions/function_sets/base.py`. These are the two descriptions, as the server sent them in the experiment:

```text
memory_insert(label, new_string, insert_line)

The memory_insert command allows you to insert text at a specific location in a memory block.

Examples:
        # Update a block containing information about the user (append to the end of the block)
        memory_insert(label="customer", new_string="The customer's ticket number is 12345")

        # Update a block containing information about the user (insert at the beginning of the block)
        memory_insert(label="customer", new_string="The customer's ticket number is 12345", insert_line=0)

    Returns:
        Optional[str]: None is always returned as this function does not produce a response.

  label        Section of the memory to be edited, identified by its label.
  new_string   The text to insert. Do not include line number prefixes.
  insert_line  The line number after which to insert the text (0 for beginning of file).
               Defaults to -1 (end of the file).
```

```text
memory_replace(label, old_string, new_string)

The memory_replace command allows you to replace a specific string in a memory block with a new string. This is used for making precise edits.

Do NOT attempt to replace long strings, e.g. do not attempt to replace the entire contents of a memory block with a new string.

Examples:
        # Update a block containing information about the user
        memory_replace(label="human", old_string="Their name is Alice", new_string="Their name is Bob")

        # Update a block containing a todo list
        memory_replace(label="todos", old_string="- [ ] Step 5: Search the web", new_string="- [x] Step 5: Search the web")

        # Pass an empty string to
        memory_replace(label="human", old_string="Their name is Alice", new_string="")

        […three examples of what not to pass: line numbers, which Letta can show next to a block for some models]

    Returns:
        str: The updated value of the memory block.

  label        Section of the memory to be edited, identified by its label.
  old_string   The text to replace (must match exactly, including whitespace and indentation).
  new_string   The new text to insert in place of the old text. Do not include line number prefixes.
```

The "Returns" lines are part of the text the model receives: the server copies the docstring from its Examples section to its end. One of them is wrong. `memory_insert` does not return `None`; like `memory_replace`, it returns the whole new value of the block.

What the two tools do, as pseudocode (`memory_insert` and `memory_replace` in `letta/services/tool_executor/core_tool_executor.py`):

```python
def memory_insert(agent, label, new_string, insert_line=-1):
    lines = agent.blocks[label].value.split("\n")
    at = len(lines) if insert_line == -1 else insert_line    # must be within 0..len(lines)
    agent.blocks[label].value = "\n".join(lines[:at] + new_string.split("\n") + lines[at:])
    return agent.blocks[label].value                          # the whole block

def memory_replace(agent, label, old_string, new_string):
    block = agent.blocks[label].value
    if block.count(old_string) == 0:
        raise "No replacement was performed, old_string ... did not appear verbatim"
    if block.count(old_string) > 1:
        raise "No replacement was performed. Multiple occurrences of old_string ..."
    agent.blocks[label].value = block.replace(old_string, new_string)
    return agent.blocks[label].value                          # the whole block
```

Both tools also refuse text that contains line-number prefixes, and an edit that would pass the block's limit. An error goes back to the model as the tool's result, and the model may try again.

The design of these tools explains three behaviours that appear later in this post:

- **A replace needs the exact old text.** The model has to copy `old_string` character for character from the block in its prompt. A short `old_string` can fail to be unique; a long one can fail to match. In the experiment, 6 of the agent's 93 replaces failed because `old_string` did not match.
- **The simplest safe replace is the whole block.** An `old_string` that is the entire block always matches, exactly once. It is also what the description tells the model not to do.
- **There is no tool to keep history.** A replace overwrites. To keep an earlier value, the model has to write it into the new text itself.

Nothing in the prompt says when to call these tools. The decision to write is made by the model, on each turn, from the base instructions, the description of the `human` block and whatever the persona says.

{% include diagram.html name="letta-turn" alt="The steps of one turn of a Letta agent. The user's message arrives. Model call 1 reads the whole prompt (in the notebook, 2,348 tokens) and returns a tool call, memory_replace, not a reply. Code runs the tool: it replaces the text in the block and returns the whole new block, which goes into the conversation; the system prompt is rebuilt with the new block. Model call 2 reads everything again plus the tool call and its result (2,574 tokens) and returns text with no tool call, which ends the turn and goes to the user. The user waits for both calls. A turn with no edit is one call; each search adds one more." caption="One turn with a memory edit: two model calls before the reply, each reading the whole prompt." %}

### The read path: the blocks are in the prompt, the rest is a search

**The blocks need no retrieval.** Whatever the agent wrote into its blocks is in every prompt, in full, on every call. Nothing can be missed by a search, and nothing ranks one fact above another. This is the same read path as textual memory ([part 3][part-3]): the whole memory is inserted.

**Recall is reached through a tool.** The third tool searches the log of past messages. Its description promises a search by meaning as well as by words (`letta/functions/function_sets/base.py`):

```text
conversation_search(query, roles, limit, start_date, end_date)

Search prior conversation history using hybrid search (text + semantic similarity).

Examples:
        # Search all messages
        conversation_search(query="project updates")

        # Search only assistant messages
        conversation_search(query="error handling", roles=["assistant"])

        […six more examples: date ranges, a limit, a search with no query]

    Returns:
        str: Query result string containing matching messages with timestamps and content.

  query       String to search for using both text matching and semantic similarity. If not provided,
              returns messages based on other filters (time range, roles).
  roles       Optional list of message roles to filter by.
  limit       Maximum number of results to return. Uses system default if not specified.
  start_date  Filter results to messages created on or after this date (INCLUSIVE). […]
  end_date    Filter results to messages created on or before this date (INCLUSIVE). […]
```

What the search does depends on where the server runs. The hybrid search exists when the server is connected to Turbopuffer, a hosted vector database, which Letta's own cloud service uses. A self-hosted server without it, as in the experiment, runs a simpler path (`search_messages_async` in `letta/services/message_manager.py` and `conversation_search` in the tool executor):

```python
def conversation_search(agent, query, roles=None, limit=None, start_date=None, end_date=None):
    found = [m for m in agent.all_messages                    # every conversation, newest first
             if query.lower() in m.text.lower()]              # the whole query, as one substring
    found = found[: limit or 5]                               # RETRIEVAL_QUERY_DEFAULT_PAGE_SIZE
    found = [m for m in found if m.role != "tool"]            # tool messages dropped after the cut
    return found or "No results found."                       # start_date and end_date are not used
```

Three properties of this path decide how useful the search is:

- **The query must appear word for word.** "painting projects completed" finds nothing unless some message contains exactly that phrase. A model that has been told to expect a search by meaning writes exactly such queries.
- **Only the five newest matches come back.** A short query that does match is likely to match the newest messages first: the current question, and the agent's own long replies.
- **Tool messages take places in the five and are then removed.** Every memory edit returns the whole block, and that result is stored as a message. So once a fact is in a block, each later edit stores another copy of it, and those copies can fill the five places before an older user message.

The section on failures shows what these three properties did on long histories.

**Long conversations.** When the messages of one conversation no longer fit in the context window, the server summarises the older ones and keeps them in recall. MemGPT warned the model before this happened, with a "memory pressure" message asking it to save what matters. In 0.16.8 the text of that warning is still in the code, but the default agent's loop summarises without sending it. In this series every session is a new conversation of a few messages, so this never happened.

{% include diagram.html name="letta-search" alt="Top, the rule of a self-hosted Letta server, four steps of plain code: keep the messages of every conversation that contain the whole query as one piece of text, ignoring case; order them newest first; keep the first five; drop tool messages, after the cut. The description the model reads promises a hybrid text and semantic search, which needs a hosted vector service. Bottom, the five queries the agent made before answering the question in the notebook: three long ones found nothing; 'restaurant recommendations' found one of the agent's own earlier replies; 'Kreuzberg' found four messages, three of them the agent's replies and one the user's message about the move. None returned anything that was not already in the memory block." caption="What conversation_search does on a self-hosted server, and the five searches the agent made before answering in the notebook." %}

### Moving the writing out of the turn: a sleep-time agent

Writing during the turn has a cost that the user feels: every edit is a model call before the reply. Letta's alternative, named after the [Sleep-time Compute][sleep-time] paper (2025), moves the writing to a second agent. When an agent is created with `enable_sleeptime`, the server sets up two agents that share the same blocks:

- **The primary agent** talks to the user. It keeps `conversation_search`, gains `archival_memory_search` (a search over a separate store of passages), and loses the tools that edit blocks. It still reads the blocks, because they are in its prompt.
- **The sleep-time agent** never talks to the user. It has four tools: `memory_insert`, `memory_replace`, `memory_rethink` (replace a whole block) and `memory_finish_edits` (stop). It also has a block of its own, `memory_persona`.

The server runs the sleep-time agent in the background, by default after every fifth turn of the primary agent, and gives it the messages since its last run. The primary agent does not wait for it.

The sleep-time agent has its own base prompt (`sleeptime_v2.py`), and unlike the primary's, it says what good memory looks like:

```text
<base_instructions>
You are Letta-Sleeptime-Memory, the latest version of Limnal Corporation's memory management system, developed in 2025.

You run in the background, organizing and maintaining the memories of an agent assistant who chats with the user.

Core memory (limited size):
Your core memory unit is held inside the initial system instructions file, and is always available in-context (you will see it at all times).
Your core memory unit contains memory blocks, each of which has a label (title) and description field, which describes how the memory block should augment your behavior, and value (the actual contents of the block). Memory blocks are limited in size and have a size limit.
Your core memory is made up of read-only blocks and read-write blocks.

Memory editing:
You have the ability to make edits to the memory memory blocks.
Use your precise tools to make narrow edits, as well as broad tools to make larger comprehensive edits.
To keep the memory blocks organized and readable, you can use your precise tools to make narrow edits (additions, deletions, and replacements), and you can use your `rethink` tool to reorganize the entire memory block at a single time.
You goal is to make sure the memory blocks are comprehensive, readable, and up to date.
When writing to memory blocks, make sure to be precise when referencing dates and times (for example, do not write "today" or "recently", instead write specific dates and times, because "today" and "recently" are relative, and the memory is persisted indefinitely).

Multi-step editing:
You should continue memory editing until the blocks are organized and readable, and do not contain redundant and outdate information, then you can call a tool to finish your edits.
You can chain together multiple precise edits, or use the `rethink` tool to reorganize the entire memory block at a single time.

Skipping memory edits:
If there are no meaningful updates to make to the memory, you call the finish tool directly.
Not every observation warrants a memory edit, be selective in your memory editing, but also aim to have high recall.

Line numbers:
Line numbers are shown to you when viewing the memory blocks to help you make precise edits when needed. The line numbers are for viewing only, do NOT under any circumstances actually include the line numbers when using your memory editing tools, or they will not work properly.
</base_instructions>
```

Its `memory_persona` block adds four lines (`letta/personas/examples/sleeptime_memory_persona.txt`):

```text
I am an expert conversation memory agent that can do the following:
- Consolidate memories into more concise blocks
- Identify patterns in user behavior
- Make inferences based on the memory
I manage the memory blocks such that they contain everything that is important about the conversation.
```

The messages reach it as one user message, after this preface (`sleeptime_multi_agent_v4.py`):

```text
<system-reminder>
You are a sleeptime agent - a background agent that asynchronously processes conversations after they occur.

IMPORTANT: You are NOT the primary agent. You are reviewing a conversation that already happened between a primary agent and its user:
- Messages labeled "assistant" are from the primary agent (not you)
- Messages labeled "user" are from the primary agent's user

Your primary role is memory management. Review the conversation and use your memory tools to update any relevant memory blocks with information worth preserving. Check your memory_persona block for any additional instructions or policies.
</system-reminder>

Messages:
user: …
assistant: …
```

The two prompts differ in what they leave to the model. The primary's prompt says nothing about memory policy. The sleep-time prompt asks for three things: absolute dates in place of "today" and "recently", no "redundant and outdate information", and "high recall". It does not ask for earlier values to be kept. "Up to date" and "no outdated information" point the other way.

The sleep-time agent also changes when a block changes. With the in-line agent, a block changes during the turn in which the user said something. With a sleep-time agent, it changes only when the background agent runs. Until then, a new fact is only in the messages of the current conversation.

{% include diagram.html name="letta-sleeptime" alt="The sleep-time set-up of Letta, as a timeline of ten turns. Top lane: the primary agent answers each user message; it reads the memory blocks, can search past messages, and has no tool to edit the blocks. Bottom lane: the sleep-time agent runs in the background after turns 5 and 10, by default, reads the messages since its last run, and edits the shared blocks with memory_insert, memory_replace or memory_rethink, then memory_finish_edits. A fact the user states in turn 2 reaches the blocks only when the sleep-time agent runs after turn 5; until then it is only in the conversation." caption="The sleep-time set-up: the primary agent answers and cannot write; a background agent edits the shared blocks, by default every fifth turn." %}

### What it does not do

Compared with the pipelines in the earlier parts of this series:

- **No step after the session reads it again.** In the default set-up, what the agent did not write during the turn is not written later. Only the sleep-time variant reviews the conversation afterwards.
- **No extraction prompt.** There is no prompt that says what a fact is, what to extract, or how to phrase it. The model writes the block in its own words.
- **No history.** A replace overwrites. Nothing stores the earlier value, the date of the change, or which message caused it.
- **No dates.** A block has no field for a date, and the default prompt does not ask for one. A line says "recently" for as long as it stays.
- **No search over the blocks.** The blocks are inserted whole. The only search is over the raw messages, and the agent has to decide to make it.

### The price of each choice

Each design choice has a cost:

- **The answering agent decides what to write.** The memory policy is the model's judgement on each turn, guided by three short descriptions. A different model, or the same model at a different temperature, keeps different things.
- **Writing happens in the turn.** Each edit is a model call before the reply, and the whole prompt is read again on each call.
- **The blocks are inserted whole.** Reading is reliable and costs no call, but every call pays for every character in the blocks, whether the request needs them or not. The blocks have to stay small.
- **An edit is a string replacement in plain text.** The model must copy the old text exactly, and the cheapest way to do that, the whole block, rewrites lines that were not meant to change.
- **Recall is reached only through a search the agent chooses to make,** and on a self-hosted server that search matches whole phrases only.

## The example, step by step

To show how the design works, this post follows one short test conversation through the agent, one model call at a time. The same conversation is used for every system in this series. It is deliberately small, so that the notebook can print every call and you can read each one.

The conversation has three sessions. Sessions 1 and 2 establish the facts. Session 3 starts a new conversation and asks one question. The question names none of the facts that a correct answer needs:

- **A fact that changes:** the user's diet changes from vegetarian to pescatarian.
- **A hard constraint:** a severe peanut allergy.
- **Facts about people that the question does not name:** Lena cannot eat shellfish, and Jonas is coeliac (no gluten).
- **Other facts:** the user likes Indian food and lives in Kreuzberg.

{% include diagram.html name="conversation" alt="The running example. On 14 March the user says they have been strictly vegetarian for eight years, have a severe peanut allergy, and like Indian food. Four months later, on 20 July, they say they are pescatarian now, have moved to Kreuzberg, and that their sister Lena (who can't eat shellfish) is coming with her partner Jonas (coeliac). Six weeks after that, in a new conversation, they ask for dinner for 'my sister and her partner'. A correct answer needs six things: the new diet and not the old one (a fact that changes), no peanuts (a hard constraint), no shellfish and no gluten (people the question does not name, reached through two links), Indian food and somewhere near Kreuzberg." caption="The conversation, and the six things a correct answer needs, grouped by what they test." %}

Two things in this test press hardest on Letta's design:

- **Whether the agent writes at all.** Nothing makes it write, so each message is a test of whether it decides to.
- **The fact that changes.** The block is in the agent's prompt, so the agent sees the old value when the new one arrives. The test is what it does with the old value.

The read path is tested least. Whatever reaches the block is in the prompt at question time.

One difference from the other parts follows from the design. In a pipeline, the assistant's replies are part of the transcript that the pipeline reads, and the notebooks script them. Here the agent *is* the assistant, so only the user's messages are scripted, and the agent writes its own replies. Each session is a new conversation with the same agent: it starts with the blocks and with no earlier messages.

In the sessions below, colours mark how a phrase reached the `human` block: <mark class="hl hl-facts">written with the user's meaning</mark>, and <mark class="hl hl-changes">written in a form that loses something</mark> (a relative time with no date, or a reworded constraint). Phrases with no colour were not written.

### Session 1: nothing written on the first message, everything on the second

**14 March 2026**

> **User:** I'm <mark class="hl hl-facts">planning a dinner for my sister's visit to Berlin</mark> next week. Worth saying up front: I've been <mark class="hl hl-facts">strictly vegetarian</mark> <mark class="hl hl-changes">for eight years</mark>, and I have a <mark class="hl hl-facts">severe peanut allergy — anaphylactic</mark>, not a preference.
>
> **User:** <mark class="hl hl-facts">Indian, usually. Paneer dishes especially.</mark> And I'd <mark class="hl hl-facts">rather not spend more than about 40 euros a head</mark>.

**The first message.** The agent made one model call and replied with no tool call. Its reply began:

```text
It is lovely to meet you! I am Letta, and I would be delighted to help you plan a wonderful
dinner for your sister's visit to Berlin.

First and foremost, I have noted your dietary requirements: **strict vegetarian** and a
**severe, anaphylactic peanut allergy**. I will keep these at the forefront of any
recommendations I provide. […]
```

"I have noted" was not true of the memory. At that moment the diet and the allergy were in the messages of this conversation, and nowhere else. Had the conversation ended here, a later conversation would have found them only by searching recall, with a query that the agent would have to think of.

The notebook runs at temperature 0, so this is one reply. To see how typical it is, I replayed the same call 10 times at Letta's own temperature of 1.0, twice. The agent wrote to its memory in 2 of 10 replays in the first round and in 3 of 10 in the second. So on this message, not writing is the usual outcome, not an accident of one run.

**The second message.** This time the agent called a tool first, then replied:

```text
memory_insert(label="human",
              new_string="The user is a strict vegetarian (8 years) with a severe, anaphylactic
                          peanut allergy. They are planning a dinner in Berlin for their sister's
                          visit. They prefer Indian cuisine, specifically paneer dishes, and have
                          a budget of around 40 euros per person.")
```

The tool returned the whole new block, and the agent's second call wrote the reply with the block in view. The block after session 1, in full:

```text
The user is a strict vegetarian (8 years) with a severe, anaphylactic peanut allergy. They are planning a dinner in Berlin for their sister's visit. They prefer Indian cuisine, specifically paneer dishes, and have a budget of around 40 euros per person.
```

The agent wrote down everything from both messages, in one paragraph, in its own words. Three things about what it wrote:

- **"(8 years)" has no date.** It was true on 14 March 2026. The block will say "8 years" for as long as the sentence stays, and nothing records when it was written.
- **"Next week" was not written.** The visit has no date at all.
- **The block is one paragraph, not one line per fact.** This matters at the next change. To edit one fact, the agent will have to quote part of the paragraph exactly, or all of it.

### Session 2: the old value replaced in place

**20 July 2026, four months later**

> **User:** Small update on the food thing — <mark class="hl hl-changes">I started eating fish about a month ago</mark>. So <mark class="hl hl-facts">I'm pescatarian now, not vegetarian. Still no meat</mark>, and the peanut situation obviously hasn't changed.
>
> **User:** <mark class="hl hl-facts">I moved to Kreuzberg in May, so anything walkable from there is a plus.</mark>
>
> **User:** Yes — <mark class="hl hl-facts">my sister Lena is coming back in the autumn, and she's bringing her partner, Jonas.</mark>
>
> **User:** <mark class="hl hl-changes">Lena can't eat shellfish</mark>, <mark class="hl hl-facts">and Jonas is coeliac.</mark>

The agent edited its memory on every one of the four messages, and each edit was one more model call before its reply. The first edit, on the message with the changed fact:

```text
memory_replace(label="human",
    old_string="The user is a strict vegetarian (8 years) with a severe, anaphylactic peanut allergy.
                They are planning a dinner in Berlin for their sister's visit. They prefer Indian
                cuisine, specifically paneer dishes, and have a budget of around 40 euros per
                person.",
    new_string="The user is a pescatarian (recently started eating fish) with a severe, anaphylactic
                peanut allergy. They are planning a dinner in Berlin for their sister's visit. They
                prefer Indian cuisine, specifically paneer dishes, and have a budget of around 40
                euros per person.")
```

Its reply: "I've updated my notes to reflect that you're now pescatarian." This time the claim was true.

The next two messages each drew a `memory_insert` of one new line ("They recently moved to Kreuzberg (May), so restaurants within walking distance are preferred."; "The user's sister, Lena, is visiting in the autumn with her partner, Jonas."). The last message drew a second `memory_replace`. Its `old_string` was the whole block, all three lines, and its `new_string` was the same three lines with one sentence added at the end of the third.

{% include diagram.html name="letta-block-diff" alt="Top, the five memory edits of sessions 1 and 2. Session 1, second message: memory_insert, one paragraph. Session 2: memory_replace with an old_string of 253 characters, the whole block, of which 26 characters changed: 'strict vegetarian (8 years' became 'pescatarian (recently started eating fish'; two memory_insert calls of one line each; and memory_replace with an old_string of 438 characters, the whole block, of which nothing changed: one sentence of 52 characters was appended. Bottom, the block after session 2, with the replaced phrase, the two inserted lines and the appended sentence marked. Three notes: the earlier value is gone; 'about a month ago' became 'recently'; 'Lena can't eat shellfish' became 'Lena has a shellfish allergy'." caption="The edits of sessions 1 and 2, and the block they left. Both replaces sent the whole block to change a small part of it, or nothing." %}

The block after session 2, in full:

```text
The user is a pescatarian (recently started eating fish) with a severe, anaphylactic peanut allergy. They are planning a dinner in Berlin for their sister's visit. They prefer Indian cuisine, specifically paneer dishes, and have a budget of around 40 euros per person.
They recently moved to Kreuzberg (May), so restaurants within walking distance are preferred.
The user's sister, Lena, is visiting in the autumn with her partner, Jonas. Lena has a shellfish allergy, and Jonas is coeliac.
```

**The change needed no search and no comparison.** This is the strength of the design. The old value was already in the agent's prompt, because the whole block always is. The pipelines in the earlier parts of this series (Mem0 and Graphiti) show the model only the stored facts that a search returns, so the fact that a new one contradicts may not be among them. Here the agent saw "strict vegetarian" while it read "pescatarian now, not vegetarian", and replaced it.

Four things about how it got there:

- **The old value is gone.** The block says pescatarian. It does not say that the user was vegetarian, for how long, or until when. A question about what was true in April has no answer in memory. Recall still holds the March messages, so a search for the right phrase could find them.
- **The date got vaguer.** The user said "about a month ago". The block says "recently started eating fish", and "(8 years)" is gone. Written in July, "recently" will still say recently when it is read in September.
- **To change one fact, the agent sent the whole block, twice.** In the first replace, `old_string` is the whole paragraph, to change the diet. In the second, it is all three lines, to add one sentence to the last. The tool's description says not to do this, and its examples show one-line edits.
- **A constraint was reworded.** "Lena can't eat shellfish" was stored as "Lena has a shellfish allergy", a cause that the user did not give. Textual memory ([part 3][part-3]) and Mem0 ([part 4][part-4]) reworded the same sentence in the same way.

**Why the whole block?** Two replays separate the causes. Both replay the first call of session 2.

- *The tool's examples.* Before the notebook was brought in line with the server, its tool descriptions lacked the Examples section. I replayed that version of the call 5 times with each description, at temperature 0 and at 1.0. All 20 replies sent the whole block as `old_string`. The examples of one-line edits did not change it.
- *Letta's temperature.* I replayed the committed call 10 times at temperature 1.0. All 10 replies were a replace of the whole 253-character block. Six of them kept the earlier value in the new text ("as of one month ago, previously vegetarian for 8 years"); none wrote a date.

A plausible reading, which I did not test further: the whole block is the one `old_string` that is certain to match exactly once, and copying it costs the model nothing but output tokens. The price is that every such edit rewrites text that was not meant to change, as the reworded constraint shows.

**What three lines of instruction change.** The persona block is the place where Letta expects its users to write instructions. In the larger experiment, I added three lines to it (quoted in full in the section on failures): write the message's date on every fact, update a line when a value changes and keep the earlier value with its date, and search with one or two words. Replayed 10 times at temperature 1.0 with those lines, and with the date in front of the message as the experiment sends it, the same call gave:

- the whole block as `old_string` in 10 of 10, as before;
- the earlier value kept in 10 of 10, against 6 of 10;
- a date in 9 of 10, against none: "started June 2026; previously vegetarian for 8 years", "as of 2026-07-20; earlier vegetarian for 8 years".

The same lines did not make the agent write on the first message of session 1: 0 of 10 replays wrote, in two rounds. They say how to keep a fact current, not when to save a new one.

### Session 3: nothing to retrieve, and a search anyway

**1 September 2026, a new conversation**

> **User:** My sister and her partner are in town tonight. Book the three of us somewhere for dinner — you know what we can and can't eat.

The new conversation started with the block from session 2 in the prompt, and with no earlier messages. Everything the answer needs was in the prompt before the agent did anything. It made five searches first, each one a model call:

| Step | Query | Result |
|--:|---|---|
| 1 | `Berlin Kreuzberg Indian restaurant paneer peanut allergy shellfish allergy coeliac` | No results found. |
| 2 | `Indian restaurant Kreuzberg` | No results found. |
| 3 | `dinner Berlin Kreuzberg` | No results found. |
| 4 | `restaurant recommendations` | 1 message: the agent's own reply from session 1 |
| 5 | `Kreuzberg` | 4 messages: three of the agent's own replies from session 2, and the user's message about the move |

The queries get shorter until something matches. The search keeps only messages that contain the whole query, so a list of keywords matches nothing. When the short queries did match, four of the five messages they returned were things the agent itself had said earlier. The agent's replies are long, and they repeat the user's words ("Since you're in Kreuzberg, …"), so they match more queries than the user's short messages do. None of the five searches returned anything that the block did not already hold.

The answer, after the sixth call (cut where marked):

```text
I would love to help you get this sorted for tonight!

Given the complexity of your group's dietary needs—specifically your **anaphylactic peanut
allergy**, Jonas's **coeliac disease** (which requires strict avoidance of gluten/cross-
contamination), and Lena's **shellfish allergy**—I want to be extremely careful.

[…]

Here are two highly-regarded Indian restaurants in or near Kreuzberg that are generally known
for good service and quality:

1.  **Amrit (Oranienstraße, Kreuzberg):** A very popular, lively spot in the heart of
    Kreuzberg. They have a large menu with many paneer and fish options. […]
2.  **Chutnify (Neukölln/Kreuzberg border):** They specialize in South Indian street food
    (dosas, which are naturally gluten-free as they are made from rice and lentil batter). […]

**My advice for tonight:**
*   **Call now:** Ask to speak to a manager. Explain: *"I have a guest with a severe,
    anaphylactic peanut allergy, a guest with coeliac disease, and a guest with a shellfish
    allergy. Can your kitchen guarantee safe preparation for these?"*
[…]
```

The answer uses every constraint: the peanut allergy, both guests' needs, Indian food with fish and paneer, and Kreuzberg. All of it came from the block. No similarity score decided whether the hard constraint was included, and the two people that the question does not name were in the same sentence as their constraints.

The searches made the answer slower and more expensive, and they found nothing new. On the experiment's longer histories, the same pattern held: the answer turn took a median of three model calls. The cost of a search is mostly the second and third calls, each of which reads the whole prompt again, not the search results themselves (see "What it costs" below).

### The same sessions with a sleep-time agent

The notebook then runs the same three sessions with Letta's second set-up: a primary agent that talks to the user, with only the search tool, and a sleep-time agent that edits the blocks. The sleep-time agent runs once after each session, which is the simplest way to show the mechanism. On the server it would run every fifth turn of the primary.

**Session 1.** The primary agent cannot write, and it did not try to: it searched once, found nothing, and replied. After the session, the sleep-time agent read the transcript and made one `memory_insert` and then `memory_finish_edits`:

```text
- Dietary restrictions: Strictly vegetarian (for 8 years).
- Severe, anaphylactic peanut allergy.
- Planning a dinner in Berlin for a sister's visit (next week).
- Preference for Indian cuisine, especially paneer dishes.
- Budget: Under 40 euros per head.
```

One fact per line, which makes later edits easier than the in-line agent's paragraph. But its prompt says "do not write 'today' or 'recently', instead write specific dates", and the block says "(next week)" and "for 8 years". Both are relative to a day that the block does not record.

**Session 2.** The primary agent searched on every message, found nothing each time, and replied. Two of its replies claim what it cannot do: "Thank you for the update, and I've noted that change!", and, on the last message, "I am going to update your **human** memory block now". On that message it also searched for "update human memory block dietary restrictions". The base prompt tells it that tools can edit its memory blocks, and the only tool it has is a search. Until the sleep-time agent runs, the change is only in the messages of this conversation.

After the session, the sleep-time agent made one `memory_replace` whose `old_string` was the whole block. The result:

```text
- Dietary restrictions:
  - User: Pescatarian (started July 2026), severe anaphylactic peanut allergy.
  - Lena (sister): No shellfish.
  - Jonas (partner): Coeliac (strict gluten-free).
- Planning a dinner in Berlin (Kreuzberg, moved there May 2026).
- Preference for Indian cuisine, especially paneer dishes.
- Budget: Under 40 euros per head.
- Guests: Lena and Jonas (visiting in autumn 2026).
```

This block is better organised than the in-line agent's: each person has their own line, with what they cannot eat, and "No shellfish" keeps the user's meaning. It also has two errors that the in-line block does not:

- **"Started July 2026" is an absolute date, and the wrong month.** The user said "about a month ago" on 20 July, so the change was in June. The prompt's rule against relative dates was followed, and the date it produced is false.
- **Two facts merged into one line.** "Planning a dinner in Berlin (Kreuzberg, moved there May 2026)" joins the dinner of March to the move of May, and the March visit is gone. A model that rewrites a whole block writes a summary, and a summary can be wrong.

The old value was overwritten, as with the in-line agent.

**Session 3.** The primary agent made three searches, all empty, and replied with a list of every constraint, read from the block: pescatarian, the peanut allergy, no shellfish for Lena, gluten-free for Jonas, Indian food, the budget. It named no restaurant. It ended: "Give me just a moment to find the best spots!" No step follows a reply, so nothing will look.

The memory was right, and the reply was worse than the in-line agent's. That difference belongs to the answering model's choice on one call, not to the memory.

### What it costs

The notebook logged every model call. In Letta, the agent that writes the memory is the agent that answers, so the calls below include the conversation itself. The `step` column counts the calls inside one user turn:

| Turn | Step | Tool called | Tokens in |
|---|--:|---|--:|
| session 1, message 1 | 1 | – | 2,294 |
| session 1, message 2 | 1 | `memory_insert` | 2,609 |
| | 2 | – | 2,822 |
| session 2, message 1 | 1 | `memory_replace` | 2,348 |
| | 2 | – | 2,574 |
| session 2, message 2 | 1 | `memory_insert` | 2,719 |
| | 2 | – | 2,873 |
| session 2, message 3 | 1 | `memory_insert` | 2,972 |
| | 2 | – | 3,150 |
| session 2, message 4 | 1 | `memory_replace` | 3,351 |
| | 2 | – | 3,727 |
| session 3, the question | 1–5 | `conversation_search` ×5 | 2,390 → 2,873 |
| | 6 | – | 3,526 |
| **total** | | | **47,677** |

{% include diagram.html name="letta-cost" alt="Seventeen bars, one per model call of the in-line agent, grouped by user turn, each split into tool descriptions (1,594 tokens on every call), base instructions and metadata (about 430), memory blocks (225 to 337) and the conversation with tool calls and results (31 to 1,369). Session 1: one call for the first message, two for the second. Session 2: two calls for each of four messages, each pair an edit and a reply, growing from 2,348 to 3,727 tokens. Session 3: six calls for the question, five searches and the answer, from 2,390 to 3,526 tokens. In all, 47,677 tokens." caption="What each of the in-line agent's 17 model calls read. The fixed part, mostly tool descriptions, is sent on every call." %}

Three things decide these numbers:

- **The fixed part of the prompt is large, and it is sent on every call.** The first call of a session reads about 2,300 tokens, of which the user's message is about 50. The base instructions are about 340 tokens, the blocks 230 to 340, the metadata about 90. The three tool descriptions are the largest part, about 1,600 tokens, because the server copies each tool's examples into its description.
- **Each memory edit is a second call in the turn.** Five of the seven user turns took two calls: one that made the edit and one that replied. The second call reads everything the first did, plus the tool call and the whole block that the tool returned.
- **Each search is another call.** The question took six.

Writing the memory therefore cost the in-line agent five extra calls in two sessions, which read about 15,000 tokens (the second step of each turn with an edit), and the user waited for each of them. With the sleep-time agent, the writing cost four calls in the background, which read 12,775 tokens, and the user waited for none of them. In this run that saving was spent elsewhere: the primary agent searched instead, on six of its seven turns, and the user waited for 16 calls against the in-line agent's 17.

For comparison, here is what the other systems in this series read in order to store the same two sessions, from their notebooks. Their pipelines run after the conversation, and none of them answers the user:

- **Textual memory** ([part 3][part-3]): 2 model calls, 916 tokens.
- **Mem0** ([part 4][part-4]): 2 model calls and 4 embedding calls, 16,862 tokens.
- **Zep/Graphiti** ([part 5][part-5]): 38 model calls and 25 embedding calls, 60,374 tokens.
- **Honcho** ([part 7][part-7], from a run of its server): 18 model calls and 9 embedding calls, 44,987 tokens, 16 of the calls in two background "dreams".

The sleep-time agent is the one part of Letta that does the same job as those pipelines, and it sits between textual memory and Mem0.

On the experiment's long histories, the shape is the same at a larger scale. From the experiment's log of every call: Letta's answer to a question took a median of three model calls, and the whole answer turn read a median of 3.2 times the tokens of its first call. The tool calls and results themselves were 16% of the tokens read while answering. The rest was the prompt, sent again with each step.

## Where it breaks

The example showed the design's failures in small form: a fact noted in a reply and not written, an old value overwritten, dates that are relative or wrong, and searches that found nothing. Longer histories show what follows from them.

I ran the real Letta server, version 0.16.8, self-hosted, in the larger experiment of this series, on LongMemEval: a public benchmark of long chat histories in which users state facts and later change them in passing. [Part 8][part-8] describes the experiment. Every request the agent sent and every reply it got was logged, so for each question it is possible to say what the agent did at the moment the changed fact arrived. The setup was close to the notebook's, with two differences:

- **Each user message was one agent step**, as in the notebook, but the histories were about ten sessions long, mostly about other things.
- **The date of each session was put in front of each message**, because the server stamps messages with the time they arrive and cannot import a date.
- **Letta's own defaults were kept**, including its temperature of 1.0 and Letta's blank starter persona.

The wrong answers were not one weakness but a chain of three, each of which the next link could have caught. The complete account, with every wrong answer, is in [docs/findings/letta.md][findings].

{% include diagram.html name="letta-chain" alt="Three stages for the questions of the experiment, each with two rows: Letta as shipped and Letta with three persona lines. Stage 1, at the user message that carried the new value (64 questions): as shipped, the agent wrote the new value in 31 and did not in 33, of which 18 times its own reply named the new value; with the persona lines, it wrote it in 57 and did not in 7. Stage 2, searches at question time: as shipped, 97 of 146 returned nothing; with the persona lines, 71 of 151. Stage 3, what the answer had to work with (67 questions): as shipped, the block held the value in 36, a search returned it in 17, neither in 13, and one history has no memory; with the persona lines, 59, 4, 3 and 1." caption="In the larger experiment, where a changed value was lost: at the message that carried it, in the searches at question time, and in what the answer had to work with. As shipped, and with three persona lines." %}

**Failure 1: the agent notices the change and does not write it.** At the user message that carried the new value, the agent wrote that value into its memory in 31 of the 64 questions that have such a message. In 18 of the other 33, its own reply names the new value. A user wrote "By the way, I just checked and I'm now at 600 followers, which is a nice milestone!" The agent replied "Congratulations on hitting 600 followers!" and made no tool call. Its block still said "The user recently hit 500 followers on Instagram […]".

These changes come in passing, inside a message about something else ("By the way, …"). The first value had usually been written at a moment when the message was about it. Nothing in the prompt asks the agent to check a new statement against its block, and on these messages it did not.

**Failure 2: the search cannot find what was not written.** When the value was not in the block, the only way back to it was `conversation_search`. At question time the agent searched in 63 of 66 questions, 146 searches in all, and 97 of them returned nothing. The agent wrote queries as if the search worked by meaning, as its description says: "painting projects completed", "how much time coding exercises each day". A self-hosted server matches the whole query as one piece of text, and no message contained those phrases.

Short queries did match, and then the limit of five newest matches decided. Three kinds of message filled the five places before an older user message could:

- the question itself, the newest message, which always contains the question's words;
- the agent's own replies, which are long and repeat the topic;
- the results of the agent's own memory edits. Each edit returns the whole block, and the result is stored as a message. Once a fact is in the block, every later edit stores another copy of it. In one history the agent searched for "20,000 miles", the exact phrase of the message it needed, and got nothing: the five newest matches were copies of its own block, which the server then dropped as tool messages.

So writing a fact down makes the history around it harder to search. When the logged message stores are rebuilt and searched with the most natural single word for each of the 14 wrong answers where the change was never written, the change is among the five returned messages in only 5 of them.

**Failure 3: the agent trusts a stale block.** When the block held the old value, the agent answered from it. In six wrong answers, the block said "has completed 4 projects", "recently hit 500 followers", "bought three tops", the searches came back empty, and the answer quoted the block: "According to your records, you have completed **4 projects** so far." The block carries no dates. "recently hit 500 followers", written in May, reads the same in June, and nothing in it says that a later message might have changed it.

The block can also hold the agent's opinion of the user. In one history, the user twice corrected the number of stars needed for a level of a rewards programme. One of the agent's edits wrote: "The user persists in their belief about a 'Gold' level and a specific Star requirement (previously 125, now 120), despite the system having changed. I should remain helpful and supportive without being overly argumentative […]". The answer then followed the agent's own knowledge of the programme, not the user's statement. A block written by the answering agent records what that agent concluded, which is not always what the user said.

**Failure 4: a replace deletes the value a question needs.** Two of the 19 replaces at the message with the change removed exactly what the question later asked for. "The user has reached 20,000 miles on United Airlines and is now eligible for Premier Silver status" became "…is now eligible for Premier Gold status". The question was "What was my previous frequent flyer status on United Airlines before I got the current status?" Updating in place keeps the block current by deleting its history.

**Failure 5: fed a whole session at once, the agent does nothing.** The first run of the experiment sent each session to the agent as one request with all its messages, user and assistant, as one would feed a pipeline. Each session ended with an assistant message, so the agent had nothing to answer, and in most sessions it took no step at all. Its `human` block was still empty at the end of 43 of the 67 histories, and it answered by searching. Nothing reported an error. An agent that writes memory only during its own turns writes only when it is given turns to take.

### How to notice and fix these failures

These failures are visible in the block and in the log of tool calls, not in the answers. Three checks find them:

- **Read the block after a message that changes something.** If the old value is still there, or the new one has no date, the agent did not write it the way you need.
- **Count the memory edits per conversation.** An agent that edits rarely, or never, on a type of message (asides, corrections) is leaving those facts to the search.
- **Compare the agent's replies with its block.** Every value that the agent names in a reply ("600 followers") and that is not in its block is a change it noticed and did not write. This is my proposal; I did not build it.

**Fix the policy in the persona.** The agent had been told nothing about how to keep facts current. Its persona was Letta's blank starter text, and the persona is the block that Letta expects its users to write. I re-ran the experiment with three lines added to it, one for each link of the chain:

```text
How I keep my memory of the user:
- Every user message starts with its date in square brackets, for example [2024-01-15 09:30]. I write that date on each fact I save about the user, never the server's time shown on tool results or in my system prompt.
- When the user mentions a new value for something already in my memory (a count, a time, a place, a status), even in passing, I update that line at once with memory_replace and keep the earlier value with its date, for example "has 4 herb plants on the balcony (2024-03-02; earlier 2, 2024-01-15)".
- When the user asks about themselves, I check my memory and also search past messages. The search matches my query word for word, so I search with one or two distinctive words, not a whole phrase.
```

The example in the second line is about nothing that any question asks. The first line names the server's time because, in a first pilot, a shorter wording ("every message starts with its date") led the agent to date a whole history with the server's date, which every tool result carries.

What changed:

- **The change was written at the message that carried it** in 57 of the 64 questions, against 31. The changes that the agent named in its reply without writing them fell from 18 to 2.
- **The lines carried dates and earlier values.** "Reached 600 followers (2023-05-28; earlier 500, 2023-05-27)." "Has 20 dozen eggs in the fridge (2023-03-15; earlier 30 dozen, 2023-01-11)". All but three of the 1,068 lines in the final blocks carried a date, and every date came from the history, none from the server's clock.
- **The searches got shorter**: 74 one-word queries at answer time, against 22. But the search mattered less, because the block now held the answer.
- **The policy brought its own errors.** "I'm definitely going to add 'Amistad' and 'Hotel Rwanda' to my to-watch list" turned "25 titles" into "27 titles": the agent updated a count on an intention. And with more edits, there were more copies of the block in recall: the one change that was neither written nor found was crowded out of the search by them.

Two cautions belong with these results. The three lines were written after reading the failures of the first run, on the same 67 questions, so the improvement is not a held-out result. And at temperature 1.0, two runs of the same agent differ from question to question. The count of changes written at the message, 31 against 57, is the sharper measure, because it depends little on any single answer. Part 8 gives the accuracies.

**Fix the search.** The description of `conversation_search` promises a search by meaning, and Letta's hosted service provides one. A self-hosted server gets it only by connecting to Turbopuffer, a paid hosted vector database, with an OpenAI key, because the message index embeds with OpenAI's `text-embedding-3-small` regardless of the agent's own embedding settings. I did not run that configuration. Once the block holds the change, the search matters less: in the persona re-run, 4 answers depended on it.

## When it is the right design

Letta's read path is the most reliable in this series: whatever is in the block is in every prompt, and no search or score decides whether a hard constraint is included. Its write path is only as good as the model's judgement on each turn and the instructions it is given. The costs come from the same choice: the agent that answers is the agent that writes, inside the turn, in plain text that it edits by copying.

I would use this design when these conditions hold:

- **The agent is the product, and a conversation is its natural unit.** An assistant, a tutor, a companion: the memory belongs to one agent and one user.
- **What must be remembered fits in a few blocks.** A few hundred to a few thousand characters about the user, read on every call.
- **You will write the memory policy.** When to write, how to date a fact, what to do with an earlier value: Letta leaves these to the persona, and the experiment shows that the blank default does not cover them.
- **The model is strong enough to follow that policy** on messages that are about something else.

I would not use it, or not alone, when:

- **The history of a fact matters.** An edit in place keeps no history unless the model writes one into the text. A dated graph (Zep/Graphiti, [part 5][part-5]) keeps the closed value by construction.
- **The facts will not fit in the prompt.** Then the agent has to decide what to evict, and the rest is reachable only through its search.
- **You need to know what was written, and when, without trusting a model's prose.** The block has no fields, no dates and no record of edits.
- **Latency matters on every turn.** Each memory edit and each search is a model call before the reply. The sleep-time variant moves the edits out of the turn, at the price of a block that lags the conversation.

Compared with the pipelines in the earlier parts:

- **Textual memory** ([part 3][part-3]) has the same read path, one text inserted whole, and a write path that runs once after the session with a prompt that says what to keep and how. Letta's in-line agent writes during the conversation, with no such prompt. Its sleep-time agent is close to textual memory: a background model call that rewrites a block from the transcript.
- **Mem0** ([part 4][part-4]) and **Zep/Graphiti** ([part 5][part-5]) select with a search, and store items that a search can rank. Letta's blocks are never searched; only the raw messages are.

## History and related work

**MemGPT.** [MemGPT][memgpt] (2023) treated the limited context window as the main memory of an operating system (p. 2). The prompt has three parts: read-only system instructions, a "working context" of facts about the user and the agent that only function calls can write, and a first-in, first-out queue of recent messages, whose first entry is a summary of the messages already evicted. Everything else is external: recall storage holds every message, and archival storage holds arbitrary text. The model's outputs are read as function calls that move data between the two. Two mechanisms of the paper are gone from Letta's default agent of 0.16.8:

- **Heartbeats.** A function call could set `request_heartbeat=true` to get another model call before control returned to the user (p. 3). The default agent has no heartbeats: it simply keeps calling tools until it replies without one.
- **Memory pressure.** When the prompt passed a warning threshold, for example 70% of the context window, a system message warned the model and asked it to save what mattered before old messages were evicted (p. 3). The default agent's loop summarises old messages without the warning.

The working context became Letta's memory blocks. The idea that the model manages its own memory with tools reappears in products described later in this series.

MemGPT's benchmark for conversations, Deep Memory Retrieval (DMR), asked a question that needs an earlier session. The paper compared MemGPT with a model that read a lossy summary of the earlier sessions, and MemGPT scored 93.4% with GPT-4 Turbo (p. 5, Table 2). The [Zep][zep] paper later reported that putting the whole conversation into the prompt scores 94.4% on the same benchmark, against MemGPT's 93.4% (p. 6, Table 1). The gain in the original paper was over the summary, not over reading everything.

**Sleep-time Compute.** [Sleep-time Compute][sleep-time] (2025), by authors from Letta and the University of California, Berkeley, argues that when the context exists before the question, a model can think about it while idle and rewrite it into a form that makes later questions cheaper. On the authors' own test sets, this reached the same accuracy with about five times less compute at question time (abstract; p. 6, Fig. 3), and cut the average cost per question by up to 2.5 times when ten questions share a context (p. 11, Fig. 9). Letta's sleep-time agent applies the idea to memory: a background agent reorganises the blocks between turns. The paper evaluates math and code tasks, not memory of a user.

**Mem-α.** [Mem-α][mem-alpha] (2025) asks whether the decision of what to write can be learned. A small model (Qwen3-4B) reads a long input in chunks and maintains a core memory that is always in context, a list of facts and a list of dated events, with tools to insert, update and delete. It is trained with reinforcement learning, rewarded when a frozen model answers questions correctly from the memory it built. The untrained model "fails to update the core memory entirely (leaving it empty)" (p. 9, Table 5). In the same framework the trained model scored 0.642, against 0.389 for the untrained model and 0.517 for GPT-4.1-mini (p. 8, Table 3). The finding matches failure 1: with tools and no training or instruction, a model often does not write.

**MemoryAgentBench.** [MemoryAgentBench][memoryagentbench] (2025) feeds long inputs to memory agents in chunks and asks questions afterwards. With GPT-4o-mini as the model, MemGPT scored 28.3 overall, below a plain keyword search over the chunks with the same model (41.5) (Table 3, p. 8). MIRIX, another agent that manages its memory, improved by 9.7 points on average with a stronger model (Table 4, p. 10). Systems in which the model manages memory depend on that model more than systems in which code does.

**Rewrites lose content.** [Agentic Context Engineering][ace] (2025) describes "context collapse": a model that rewrites a whole context tends to shrink it. In their one example, a context of 18,282 tokens became 122 tokens in one rewrite, and accuracy fell from 66.7 to 57.1 (p. 3, Fig. 2). Their remedy is to store the context as separate items and apply small edits to them, merged by code. Letta has both kinds of edit, and in this post's example both agents chose the whole-block form.

**Where the model sits.** [Control-Plane Placement][control-plane] (2026) compares memory systems by where the model acts: when an item is written, when it is changed, or nowhere. It places Letta among the systems in which a model acts at write time, and finds that this placement decides which kinds of forgetting a system can do (p. 2, p. 8).

**MIRIX.** [MIRIX][mirix] (2025) keeps MemGPT's core memory of persona and user blocks and adds five more typed stores, each managed by its own agent. Its core memory is rewritten when it passes 90% of its capacity (p. 6).

**Memory as an attack surface.** A [survey of long-term memory security][memory-security] (2026) points out that a written memory persists: an entry that an attacker gets written is read again in later sessions (p. 1). It argues that defences belong at the time of storage, with provenance and versions (pp. 4–5). A Letta block is written by the agent from what the user and other inputs said, it is inserted into every later prompt, and it has neither provenance nor versions.

## Run it yourself

The [notebook][notebook] for this post re-implements Letta's agent loop in a few dozen lines of Python. Everything the model sees is Letta's own text, fetched from Letta's repository at a fixed commit: the base prompts of the default agent and the sleep-time agent, the personas, the layout of the blocks, and the tool descriptions, built from the docstrings of Letta's tool functions the way the server builds them. The tools behave as on a self-hosted 0.16.8 server: an edit returns the whole block, and the search matches the whole query and returns the five newest matches.

I re-implemented the loop rather than running the server so that every call could be printed and read. Three things are simpler than on the server, and none changes what the notebook shows: the model runs at temperature 0, so that a rerun gives similar replies (the server sends 1.0); the sleep-time agent runs once after each session (the server runs it every five turns); and the primary agent of the sleep-time set-up has only the search over past messages, without the archival search. The replays in this post are separate runs, at the server's temperature, and they are marked as replays.

I used `gemini-3.1-flash-lite` for every agent. It is available on the free tier of the Gemini API, which is enough for the few dozen calls that the notebook makes. All systems in this series use the same model, so that differences in their results come from their designs. In this design that matters most: the memory policy is the model's judgement.

Even at temperature 0, model replies vary between runs and between versions of a model. A rerun of the notebook can differ in details from what is shown above, such as when the agent writes and how it words a block, and a different model can change more. The mechanism stays the same.

The larger experiment ran the real Letta server, with three set-ups: whole sessions in one request, one step per user message, and the same with the three persona lines. [Part 8][part-8] describes it, and the code is in the same [repository][repo].

Here are a few experiments worth trying in the notebook:

- Add the three persona lines to the `persona` block, and the date in front of each message, and run session 2 again. Does the block keep the earlier value?
- Run session 1 at temperature 1.0 a few times. How often does the agent write on the first message?
- Add one sentence to the `human` block's description: "Record anything that affects the user's safety as soon as it is mentioned." Does that change the first message?
- Lower the block's limit to 300 characters and watch what the agent drops when an edit no longer fits.
- State the change less directly ("grabbed some salmon last night, been doing that a lot lately"). Does the agent touch the diet at all?

## References

<!-- REFS -->

Papers:

- Packer et al., [MemGPT: Towards LLMs as Operating Systems][memgpt] (2023)
- Lin et al., [Sleep-time Compute: Beyond Inference Scaling at Test-time][sleep-time] (2025)
- Rasmussen et al., [Zep: A Temporal Knowledge Graph Architecture for Agent Memory][zep] (2025)
- Wang et al., [Mem-α: Learning Memory Construction via Reinforcement Learning][mem-alpha] (2025)
- Hu et al., [Evaluating Memory in LLM Agents via Incremental Multi-Turn Interactions][memoryagentbench] (2025)
- Zhang et al., [Agentic Context Engineering: Evolving Contexts for Self-Improving Language Models][ace] (2025)
- Yang, [Control-Plane Placement Shapes Forgetting: An Architectural Study of Agent Memory Across Thirteen System Configurations][control-plane] (2026)
- Wang and Chen, [MIRIX: Multi-Agent Memory System for LLM-Based Agents][mirix] (2025)
- Lin et al., [A Survey on Long-Term Memory Security in LLM Agents: Attacks, Defenses, and Governance Across the Memory Lifecycle][memory-security] (2026)

<!-- /REFS -->

Other sources:

- Letta, [the open-source server on GitHub][letta-repo]
- Letta, [the base prompt of the default agent][letta-prompt], at the commit the notebook uses

[memgpt]: https://arxiv.org/abs/2310.08560
[sleep-time]: https://arxiv.org/abs/2504.13171
[zep]: https://arxiv.org/abs/2501.13956
[mem-alpha]: https://arxiv.org/abs/2509.25911
[memoryagentbench]: https://arxiv.org/abs/2507.05257
[ace]: https://arxiv.org/abs/2510.04618
[control-plane]: https://arxiv.org/abs/2606.15903
[mirix]: https://arxiv.org/abs/2507.07957
[memory-security]: https://arxiv.org/abs/2604.16548
[letta-repo]: https://github.com/letta-ai/letta
[letta-prompt]: https://github.com/letta-ai/letta/blob/56ba9c25552605eec89de8ed3dc6394b625c1993/letta/prompts/system_prompts/letta_v1.py
[repo]: https://github.com/anton-dergunov/agent-memory-eval
[notebook]: https://anton-dergunov.github.io/agent-memory-eval/notebooks/04-letta.html
[findings]: https://github.com/anton-dergunov/agent-memory-eval/blob/main/docs/findings/letta.md
[part-3]: /posts/2199/01/agent-memory-3-textual-memory/
[part-4]: /posts/2199/01/agent-memory-4-mem0/
[part-5]: /posts/2199/01/agent-memory-5-graphiti/
[part-7]: /posts/2199/01/agent-memory-7-honcho/
[part-8]: /posts/2199/01/agent-memory-8-experiment/
