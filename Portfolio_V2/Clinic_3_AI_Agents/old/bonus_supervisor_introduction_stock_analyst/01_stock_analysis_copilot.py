# BUSINESS SCIENCE UNIVERSITY
# PYTHON FOR GENERATIVE AI COURSE
# MULTI-AGENTS (AGENTIAL SUPERVISION)
# ***

# Goal: Demonstrate a simple example of Supervision with a team of agents

# NOTE: requires yfinance to get the SPY data
# NOTE: Requires Tavily API Key for Web Search (add to credentials.yml file)

# * LIBRARIES

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers.openai_functions import JsonOutputFunctionsParser

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, END

from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_experimental.tools import PythonREPLTool

from langchain.tools import tool

import operator
import functools
import os
import yaml

import yfinance 

from typing import Annotated, Sequence, TypedDict

from pprint import pprint
from IPython.display import Image, Markdown


# * LLM SELECTION

MODEL = "gpt-4o-mini"
# MODEL = "gpt-4o"

# * API KEYS

os.environ["OPENAI_API_KEY"] = yaml.safe_load(open('../credentials.yml'))['openai']

os.environ["TAVILY_API_KEY"] = yaml.safe_load(open("../credentials.yml"))['tavily']

# * Create tools

tavily_tool = TavilySearchResults(max_results=5)

python_repl_tool = PythonREPLTool()

@tool
def multiply(a, b):
    """
    This tool multiplies two numbers.
    
    Args:
        a (int): The first number.
        b (int): The second number.
    
    Returns:
        a * b (int): The product of the two numbers.
    """
    return a * b

multiply

llm = ChatOpenAI(model=MODEL)

functions = [
    {
        "name": "multiply",
        "description": "Multiplies two numbers.",
        "parameters": {
            "type": "object",
            "properties": {
                "a": {
                    "type": "integer",
                    "description": "The first number."
                },
                "b": {
                    "type": "integer",
                    "description": "The second number."
                }
            },
            "required": ["a", "b"]
        }
    }
]

multiplication_agent = llm.bind(tools=[multiply], functions=functions)

response = multiplication_agent.invoke("What is 5 times 5?")







# * Create Agent Supervisor
#   - Supervisor has 1 role: Pick which team member to send to (or if finished)

subagent_names = ["Researcher", "Coder"]

system_prompt = (
    "You are a supervisor tasked with managing a conversation between the following workers:  {subagent_names}. Given the following user request, respond with the worker to act next. Each worker will perform a task and respond with their results and status. When finished, respond with FINISH."
)

# Our team supervisor is an LLM node. It just picks the next agent to process and decides when the work is completed

# ['FINISH', 'Researcher', 'Coder']
route_options = ["FINISH"] + subagent_names 
route_options

# Using openai function calling can make output parsing easier for us
#  References: 
#   https://platform.openai.com/docs/guides/function-calling 
#   https://cookbook.openai.com/examples/how_to_call_functions_with_chat_models

function_def = {
    "name": "route",
    "description": "Select the next role.",
    "parameters": {
        "title": "route_schema",
        "type": "object",
        "properties": {
            "next": {
                "title": "Next",
                "anyOf": [
                    {"enum": route_options},
                ],
            }
        },
        "required": ["next"],
    },
}



prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages"),
        (
            "system",
            "Given the conversation above, who should act next?"
            " Or should we FINISH? Select one of: {route_options}",
        ),
    ]
).partial(route_options=str(route_options), subagent_names=", ".join(subagent_names))

pprint(dict(prompt))

llm = ChatOpenAI(model=MODEL)

supervisor_chain = (
    prompt
    | llm.bind(functions=[function_def], function_call={"name": "route"})
    | JsonOutputFunctionsParser()
)

supervisor_chain

QUESTION = "What is the last 5 years of daily history for SPY?"
result = supervisor_chain.invoke(
    {"messages": [HumanMessage(content=QUESTION)]}
)
result

result.get("next")



# * SUBAGENTS

# * Helper function

def create_agent_with_tools(llm: ChatOpenAI, tools: list, system_prompt: str):
    # Each worker node will be given a name and some tools.
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                system_prompt,
            ),
            MessagesPlaceholder(variable_name="messages"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )
    agent = create_openai_tools_agent(llm, tools, prompt)
    executor = AgentExecutor(agent=agent, tools=tools)
    return executor


# * Researcher Agent

researcher_agent = create_agent_with_tools(
    llm, 
    [tavily_tool], 
    "You are a web researcher."
)

researcher_agent

QUESTION = "What is the last 5 years of daily history for SPY?"
result = researcher_agent.invoke({"messages": [HumanMessage(content=QUESTION)]})
result

pprint(result)

Markdown(result['output'])

# * Coder Agent

coder_agent = create_agent_with_tools(
    llm,
    [python_repl_tool],
    "You may generate safe python code to analyze data and generate charts using Plotly. Please share the specific details of the Python code in your reponse using ```python ``` markdown. Please make sure to use the plotly library.",
)

coder_agent

QUESTION = "What is the last 5 years of daily history for SPY. Feel free to use yfinance library. Plot price by date using ploly? Make sure to use end date: 2024 January 10."
result = coder_agent.invoke({"messages": [HumanMessage(content=QUESTION)]})
result

pprint(result)

Markdown(result['output'])


# * Mupltiplication Tool
multiplication_agent = create_agent_with_tools(
    llm,
    [multiply],
    "You are a calculator. You can multiply two numbers."
)

multiplication_agent

QUESTION = "What is 5 times 5?"
result = multiplication_agent.invoke({"messages": [HumanMessage(content=QUESTION)]})

pprint(result)



# * LANGGRAPH

#   - NEW Skill: Annotated Sequences
class GraphState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str
    
    
def supervisor_node(state):
    
    result = supervisor_chain.invoke(state)
    
    print(result)
    
    return {'next': result['next']}

def research_node(state):
    
    result = researcher_agent.invoke(state)
    
    print(result)
    
    return {
        "messages": [AIMessage(content=result["output"], name="Researcher")],
    }
    

def coder_node(state):
    
    result = coder_agent.invoke(state)
    
    return {
        "messages": [AIMessage(content=result["output"], name="Coder")],
    }


# * WORKFLOW DAG

workflow = StateGraph(GraphState)

workflow.add_node("Researcher", research_node)
workflow.add_node("Coder", coder_node)
workflow.add_node("supervisor", supervisor_node)

for member in subagent_names:
    workflow.add_edge(member, "supervisor")
    

workflow.add_conditional_edges(
    "supervisor", 
    lambda state: state["next"], 
    {
        'Researcher': 'Researcher', 
        'Coder': 'Coder', 
        'FINISH': END
    }
)

workflow.set_entry_point("supervisor")

app = workflow.compile()

app



# * TESTING THE STOCK ANALYSIS COPILOT

      
result_3 = app.invoke(
    input = {"messages": [HumanMessage(content="Find the historical prices of SPY for the last 5 years from Yahoo Finance (feel free to use the yfinance library, which is installed). Plot a daily line chart of the SPY value over time from the historical prices using python and the plotly library. Add a 50-day and 200-day simple moving average. Make sure the end date used is '2024-07-24'. Add a dateslider.")]},
    
    config = {"recursion_limit": 10},
)

result_3

for message in result_3['messages']:
    if message.name:
        print(f"Name: {message.name}")
    print(f"Content: {message.content}")
    print("---")
    print()
    
  
result_4 = app.invoke(
    input = {"messages": [HumanMessage(content="Find the historical prices of NVDA and VIX for the last 1 year from Yahoo Finance (feel free to use the yfinance library, which is installed). Plot a daily line chart of the value over time from the historical prices using python and the plotly library. Organize the plots by using 1 column by 2 row subplots so that the dates line up and VIX is the first plot and NVDA is below. Make sure the end date used is '2024-07-24'")]},
    config = {"recursion_limit": 10},
)  

result_4

for message in result_4['messages']:
    if message.name:
        print(f"Name: {message.name}")
    print(f"Content: {message.content}")
    print("---")
    print()



import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# Define the ticker symbol and the date range
ticker_symbol = 'SPY'
end_date = '2024-01-10'
start_date = '2019-01-10'

# Get the stock data
spy_data = yf.download(ticker_symbol, start=start_date, end=end_date)

# Prepare the data for plotting
spy_data.reset_index(inplace=True)

# Create the plot
fig = go.Figure()

# Add price line
fig.add_trace(go.Scatter(x=spy_data['Date'], y=spy_data['Close'], mode='lines', name='Close Price'))

# Update layout
fig.update_layout(title='SPY Daily Closing Prices (Last 5 Years)',
                  xaxis_title='Date',
                  yaxis_title='Price (USD)',
                  xaxis_rangeslider_visible=True)

# Show the plot
fig.show()

