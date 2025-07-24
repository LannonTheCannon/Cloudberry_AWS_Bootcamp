# BUSINESS SCIENCE UNIVERSITY
# PYTHON FOR GENERATIVE AI COURSE
# MULTI-AGENTS (AGENTIAL SUPERVISION)
# ***

# CHALLENGE 4: CREATE AN APPLICATION THAT HELPS USERS ANALYZE STOCKS USING THE 01_stock_analysis_supervisor_agent

# DIFFICULTY: INTERMEDIATE

# SPECIFIC ACTIONS:
#  1. Analysis should have chat memory 
#  2. Suggest any improvements


# EXAMPLE QUESTIONS:

# What is a moving average in stock analysis?

# Make a 5-year chart of SPY. End on August 1, 2024. Add a 50-day and 200-day moving average.

# Make a 5-year chart of NVDA. End on August 1, 2024. Add Bollingerbands with a 20 day moving average

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

import streamlit as st

from langchain_community.chat_message_histories import StreamlitChatMessageHistory

from langchain_core.tools import tool
from langchain_experimental.utilities import PythonREPL

# * API KEYS

os.environ["OPENAI_API_KEY"] = yaml.safe_load(open('../credentials.yml'))['openai']

os.environ["TAVILY_API_KEY"] = yaml.safe_load(open("../credentials.yml"))['tavily']


# * STREAMLIT APP SETUP ----

st.set_page_config(page_title="Stock Analytics AI Copilot")
st.title("Stock Analytics AI Copilot")

with st.expander("I'm a complete stock analysis tool with researcher and chart coder (See more.)"):

    st.markdown(
        """
        I make it easy to visualize stock analysis with access to the `yfinance` library for stock data. I'm run by 3 agents:
        
        1. **Supervisor:** Decides which sub-agent to route tasts to. Either Researcher or Chart Coder.
        2. **Researcher:** Researches stocks, has access to web data, and helps the coder generate code to accomplish the task. 
        3. **Chart Coder:** Generates Plotly visualizations for interactive stock analysis. 
        """
    )

model_option = st.sidebar.selectbox(
    "Choose OpenAI model",
    ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
    index=0
)

MODEL = model_option

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


llm = ChatOpenAI(model=MODEL)

supervisor_chain = (
    prompt
    | llm.bind(functions=[function_def], function_call={"name": "route"})
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
    
conditional_map = {'Researcher': 'Researcher', 'Coder': 'Coder', 'FINISH': END}

workflow.add_conditional_edges("supervisor", lambda x: x["next"], conditional_map)

workflow.set_entry_point("supervisor")

app = workflow.compile()


# * STREAMLIT 

# Set up memory
msgs = StreamlitChatMessageHistory(key="langchain_messages")
if len(msgs.messages) == 0:
    msgs.add_ai_message("How can I help you?")
    
# Initialize plot and details storage in session state
if "plots" not in st.session_state:
    st.session_state.plots = []
if "details" not in st.session_state:
    st.session_state.details = []

# Function to display chat messages including Plotly charts and dataframes
def display_chat_history():
    for i, msg in enumerate(msgs.messages):
        with st.chat_message(msg.type):
            if "PLOT_INDEX:" in msg.content:
                plot_index = int(msg.content.split("PLOT_INDEX:")[1])
                st.plotly_chart(st.session_state.plots[plot_index])
                with st.expander("Chart details:"):
                    st.write(st.session_state.details[plot_index])
            else:
                st.write(msg.content)

display_chat_history()

if question := st.chat_input("Enter your question here:", key="query_input"):
    with st.spinner("Thinking..."):
        
        st.chat_message("human").write(question)
        msgs.add_user_message(question)
        
        error_occurred = False
        try: 
            result = app.invoke(
                input = {"messages": [HumanMessage(content=question)]},
                config = {"recursion_limit": 10, "configurable": {"thread_id": "1"}},
            )
        except Exception as e:
            error_occurred = True
            print(e)
        
        if not error_occurred:
            if 'chart_plotly_error' in result:
                if result['chart_plotly_error'] is False:
                    # Chart was requested and produced correctly
                    response_plot = pio.from_json(result['chart_plotly_json'])
                    
                    response_text = "## Result:\n\n"
                    for message in result['messages']:
                        if message.name:
                            response_text += f"### **Team Member:** {message.name}\n\n"
                            response_text += f"\n\n{message.content}\n"
                        response_text += "---\n"

                    # Store the plot and keep its index
                    plot_index = len(st.session_state.plots)
                    st.session_state.plots.append(response_plot)
                    st.session_state.details.append(response_text)

                    # Store the response text and plot index in the messages
                    msgs.add_ai_message(f"PLOT_INDEX:{plot_index}")

                    st.plotly_chart(response_plot)
                    with st.expander("Chart details:"):
                        st.write(response_text)
                else:
                    # Chart error occurred, return analysis text
                    response_text = "I apologize. There was an error during the plotting process. Returning the agent analysis...\n\n"
                    response_text += "## Result:\n\n"
                    for message in result['messages']:
                        if message.name:
                            response_text += f"### **Team Member:** {message.name}\n\n"
                            response_text += f"\n\n{message.content}\n"
                        response_text += "---\n"

                    # Store the response text in the messages
                    msgs.add_ai_message(response_text)
                    st.chat_message("ai").write(response_text)
            else:
                # No chart requested
                response_text = "## Result:\n\n"
                for message in result['messages']:
                    if message.name:
                        response_text += f"### **Team Member:** {message.name}\n\n"
                        response_text += f"\n\n{message.content}\n"
                    response_text += "---\n"

                # Store the response text in the messages
                msgs.add_ai_message(response_text)
                st.chat_message("ai").write(response_text)
        else:
            # An unknown error occurred
            response_text = "An error occurred. I apologize. Please try again or format the question differently and I'll try my best to provide a helpful answer."
            msgs.add_ai_message(response_text)
            st.chat_message("ai").write(response_text)