# Tool Specification Document

**Project**: Robust ReAct Agent with Self-Consistency  
**Model**: Qwen2.5-7B-Instruct (Local)  

## 1. Overview

This document defines the interface, behavior, and data schemas for the external tools available to the ReAct Agent. The agent utilizes these tools to ground its reasoning in factual data, perform precise calculations, and retrieve real-time information.

**Interaction Protocol**:

The Agent invokes tools using the following strict format in its "Action" step:
Action: tool_name[argument]
textThe System captures this output, executes the corresponding Python function, and returns the result in the "Observation" step:
Observation: [Return Value]
text## 2. Search Tools

### 2.1 wikipedia_search

**Purpose**:  
The primary source for retrieving encyclopedic knowledge and verifying static facts. Includes an auto-disambiguation mechanism to handle vague queries.

**Function Signature**: `wikipedia_search(query: str) -> str`

**Parameters**:
- `query` (Required): The search term or phrase (e.g., "Elon Musk", "Population of Tokyo").

**Returns**:
- Success: A text summary of the Wikipedia page (first 500 characters).
- Ambiguity: A list of possible options if the term is ambiguous (e.g., "Apple refers to: Apple (fruit), Apple Inc., ...").
- Failure: "No page found" or "Search timed out (>5s)".

**Constraints**:
- Timeout: Hard limit of 5 seconds to prevent agent hanging.
- Language: Defaults to English (en).

**Example Usage**:
Input: wikipedia_search[Barack Obama]
Output: Barack Hussein Obama II is an American politician who served as the 44th president of the United States from 2009 to 2017...
text### 2.2 web_search (DuckDuckGo)

**Purpose**:  
A fallback tool for retrieving real-time information (e.g., stock prices, current events, weather) that is not yet available or updated on Wikipedia.

**Function Signature**: `web_search(query: str) -> str`

**Parameters**:
- `query` (Required): The search keyword(s).

**Returns**:
- A string containing the titles and snippets of the top 3 search results concatenated together.

**Constraints**:
- Rate limited to prevent IP bans.

**Example Usage**:
Input: web_search[Apple stock price today]
Output: 1. Apple Inc. (AAPL) Stock Price, News, Quote... Price: $185.20...
2. AAPL - Apple Inc. Stock Quote - CNNMoney...
text### 2.3 hotel_search (Mock API)

**Purpose**:  
Tests the agent's ability to handle structured data (JSON) and multi-constraint queries.

**Function Signature**: `hotel_search(city: str, price_limit: int = None) -> str`

**Parameters**:
- `city` (Required): The target city (e.g., "Paris", "New York").
- `price_limit` (Optional): Maximum price per night in USD.

**Returns**:
- A JSON-formatted string listing available hotels matching the criteria.

**Behavior**:
- This is a mock function backed by a local dictionary/database.

**Example Usage**:
Input: hotel_search[Paris, 200]
Output: [{"name": "Hotel A", "price": 150, "rating": 4.5}, {"name": "Hotel B", "price": 190, "rating": 3.8}]
text## 3. Computational Tools

### 3.1 calculator

**Purpose**:  
Performs precise mathematical calculations to avoid LLM arithmetic hallucinations.

**Function Signature**: `calculator(expression: str) -> str`

**Parameters**:
- `expression` (Required): A mathematical string expression (e.g., "12 * 54", "sqrt(25)").

**Supported Operations**:
- Basic arithmetic: +, -, *, /, %
- Advanced functions: pow(x, y), sqrt(x), abs(x)

**Safety Mechanism**:
- Implemented via a sanitized Python eval(). Only whitelisted characters and functions are allowed.
- Blocks import, os, sys, and dunder methods (__).

**Returns**:
- The numerical result as a string, or an error message if the syntax is invalid.

**Example Usage**:
Input: calculator[2024 - 1946]
Output: 78
text### 3.2 compare_numbers

**Purpose**:  
A specialized tool to perform strict numerical comparison. This mitigates specific hallucinations where 7B models sometimes claim "100 is smaller than 5".

**Function Signature**: `compare_numbers(val1: float, val2: float) -> str`

**Parameters**:
- `val1`: First number.
- `val2`: Second number.

**Returns**:
- A descriptive string: "{val1} is greater than {val2}", "{val1} is less than {val2}", or "They are equal".
- Also returns the absolute difference.

**Example Usage**:
Input: compare_numbers[9.11, 9.8]
Output: 9.11 is less than 9.8 (Difference: 0.69)
text## 4. Error Handling & Guardrails

To ensure robustness, the Toolset Interface implements the following standard error responses:

| Error Type       | Trigger Condition                                      | System Response (Observation)                                      |
|------------------|---------------------------------------------------------|--------------------------------------------------------------------|
| Parsing Error    | Agent generates invalid format (e.g., Tool: name)      | Error: Invalid format. Please use Action: tool_name[args].         |
| Invalid Tool     | Agent calls a non-existent tool                        | Error: Tool '{name}' not found. Available tools: [list].           |
| Timeout          | Search takes > 5 seconds                               | Error: Search timed out. Please try a simpler query.               |
| Empty Result     | Search returns no hits                                 | Observation: No results found for '{query}'.                       |
| Math Error       | Division by zero or invalid syntax                     | Error: Invalid math expression.                                    |

## 5. Tool Selection Logic (Prompt Engineering)

The model is instructed to select tools based on the following logic map:

1. Is it a calculation? → Use **calculator**.  
2. Is it a factual question about a specific entity? → Use **wikipedia_search**.  
3. Is it about a current event or changing data? → Use **web_search**.  
4. Is it about comparing magnitudes? → Use **compare_numbers**.  
5. Is it about finding accommodation? → Use **hotel_search**.