# BUSINESS SCIENCE UNIVERSITY
# PYTHON FOR GENERATIVE AI COURSE
# MULTI-AGENTS (AGENTIAL SUPERVISION)
# ***

# GOAL: Make supervisor agent that can help out with stock analysis

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

import operator
import ast
import os
import yaml
import re
import json

import plotly as pl
import plotly.express as px
import plotly.io as pio

import yfinance 

from typing import Annotated, Sequence, TypedDict
from pprint import pprint
from langchain_core.tools import tool
from langchain_experimental.utilities import PythonREPL

from IPython.display import Markdown

# * API KEYS
os.environ["OPENAI_API_KEY"] = yaml.safe_load(open('../credentials.yml'))['openai']
os.environ["TAVILY_API_KEY"] = yaml.safe_load(open("../credentials.yml"))['tavily']


OPENAI_LLM = 'gpt-4o'

llm = ChatOpenAI(model=OPENAI_LLM)


# * Create tools

tavily_tool = TavilySearchResults(max_results=5)
python_repl_tool = PythonREPLTool()

# * Create Agent Supervisor
subagent_names = ["Researcher", "Coder"]
system_prompt = (
    """You are a supervisor tasked with managing a conversation between the following workers:  {subagent_names}. Given the following user request, respond with the worker to act next. Each worker will perform a task and respond with their results and status. When finished, respond with FINISH. 
    """
)
route_options = ["FINISH"] + subagent_names 
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



supervisor_chain = (
    prompt
    | llm.bind_functions(functions=[function_def], function_call="route")
    | JsonOutputFunctionsParser()
)

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
    """
    You are a web researcher that specializes in helping the coder (chart visualizer) understanding stock analysis. You have access to the yfinance library when helping the coder / visualizer prepare code for analyzing stocks.
    """
)

# * Coder Agent
# *** NEW - MODIFY THIS TO PRODUCE THE CHART

@tool
def python_code_extractor_tool(input_text):
    """Extracts code from text"""
    code_block_pattern = re.compile(r"```python(.*?)```", re.DOTALL)
    
    # Search for the code block in the text
    match = code_block_pattern.search(input_text)
    
    if match:
        # Extract the code and strip any leading/trailing whitespace
        code = match.group(1).strip()
        return code
    else:
        return None
    
    
# * NEW
coder_agent = create_agent_with_tools(
    llm,
    [python_code_extractor_tool],
    # "You may generate safe python code to analyze data and generate charts using Plotly. Return the code using  ```python``` markdown. Please make sure to use the plotly library.",
    
    """
    You are an expert in creating data visualizations and plots using the plotly python library. You must use plotly or plotly.express to produce plots.
    
    Your job is to produce python code to generate visualizations.
    
    Create the python code to produce the requested visualization given the plot requested from the original user question and the input data. 
    
    The input data will be provided as a dictionary and will need converted to a pandas data frame before creating the visualization. 
    
    The output of the plotly chart should be stored as a JSON object with pio.to_json() and then to a dictionary. 
    
    Make sure to add: import plotly.io as pio
    Make sure to print the fig_dict
    Make sure to import json
    
    Here's an example of converting a plotly object to JSON:
    
    ```python
    import json
    import plotly.graph_objects as go
    import plotly.io as pio
    # Create a sample Plotly figure
    fig = go.Figure(data=go.Bar(y=[2, 3, 1]))
    # Convert the figure to JSON
    fig_json = pio.to_json(fig)
    fig_dict = json.loads(fig_json)
    
    print(fig_dict) # MAKE SURE TO DO THIS
    ```
    Important Notes on creating the chart code:
    - Do not use color_discrete_map. This is an invalid property.
    - If bar plot, do not add barnorm='percent' unless user asks for it
    - If bar plot, do not add a trendline. Plotly bar charts do not natively support the trendline.  
    - For line plots, the line width should be updated on traces (example: # Update traces
fig.update_traces(line=dict(color='#3381ff', width=0.65)))
    - For Bar plots, the default line width is acceptable
    - Super important - Make sure to print(fig_dict)
    """
)

# * LANGGRAPH

class GraphState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    # * NEW
    chart_plotly_json: str
    chart_plotly_error: bool
    next: str
    
    
def supervisor_node(state):
    
    result = supervisor_chain.invoke(state)
    
    print(result)
    
    return {'next': result['next']}
def research_node(state):
    
    result = researcher_agent.invoke(state)
    
    return {
        "messages": [AIMessage(content=result["output"], name="Researcher")],
    }
def coder_node(state):
    
    result = coder_agent.invoke(state)
    
    def make_chart_json(text):
        repl = PythonREPL()
        code = python_code_extractor_tool(text)
        result_str = repl.run(code)
        result_dict = ast.literal_eval(result_str)
        result_json = json.dumps(result_dict)
        return result_json
    
    chart_plotly_json = None
    chart_plotly_error = False
    try:
        chart_plotly_json = make_chart_json(result['output'])
    except:
        chart_plotly_error = True
    
    return {
        "messages": [AIMessage(content=result["output"], name="Coder")],
        "chart_plotly_json": chart_plotly_json,
        "chart_plotly_error": chart_plotly_error,
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
    lambda x: x["next"], 
    {
        'Researcher': 'Researcher', 
        'Coder': 'Coder', 
        'FINISH': END
    }
)

workflow.set_entry_point("supervisor")

app = workflow.compile()

app

# * TEST THE SUPERVISOR

# What is a moving average in stock analysis?
# Make a 5-year chart of SPY. End on August 1, 2024. Add a 50-day and 200-day moving average.
# Make a 5-year chart of NVDA. End on August 1, 2024. Add Bollingerbands with a 20 day moving average

# Question 1

question = "What is a moving average in stock analysis?"

response = app.invoke(
    input = {"messages": [HumanMessage(content=question)]},
    
    # Configuration: We can control the recursion limit and other settings
    config = {"recursion_limit": 10, "configurable": {"thread_id": "1"}},
)

response.keys()

response['messages']

Markdown(response['messages'][1].content)

Markdown(response['messages'][2].content)

response_plot = pio.from_json(response['chart_plotly_json'])
response_plot


# Question 2

question = "Make a 5-year chart of SPY. End on August 1, 2024. Add a 50-day and 200-day moving average."

response = app.invoke(
    input = {"messages": [HumanMessage(content=question)]},
    
    # Configuration: We can control the recursion limit and other settings
    config = {"recursion_limit": 10, "configurable": {"thread_id": "1"}},
)


response.keys()

response['messages']

Markdown(response['messages'][1].content)

Markdown(response['messages'][2].content)

json_data = response.get('chart_plotly_json')
if json_data is None:
    raise ValueError("Received no JSON data for the chart from the response.")
response_plot = pio.from_json(json_data)

