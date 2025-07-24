# BUSINESS SCIENCE UNIVERSITY
# PYTHON FOR GENERATIVE AI COURSE
# MULTI-AGENTS (AGENTIAL SUPERVISION)
# ***

# Goal: Advanced application demonstrating combining everything we've learned so far:
# 1. Supervision: Multi-Agent
# 2. Product Expert RAG with Memory
# 3. Business Intelligence App with Flow Control
# 4. Marketing Agent with Prompt Engineering
# 5. LangGraph State Graph

# LangChain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from langchain_openai import ChatOpenAI, OpenAIEmbeddings

# LangGraph
from langgraph.graph import StateGraph, START, END
from typing import Annotated, Sequence, TypedDict
import operator

# Common
import os
import yaml

import pandas as pd

from pprint import pprint
from IPython.display import Markdown

# Backup to display mermaid graphs
from IPython.display import display, Image

# Sub-Agents
from marketing_analytics_team.agents.marketing_email_writer_agent import make_marketing_email_writer_agent
from marketing_analytics_team.agents.product_expert import make_product_expert_agent
from marketing_analytics_team.agents.business_intelligence_agent import make_business_intelligence_agent

# * NEW: Add Short Term Memory
from langgraph.checkpoint.memory import MemorySaver


# API Keys

os.environ["OPENAI_API_KEY"] = yaml.safe_load(open('../credentials.yml'))['openai']

# Key Inputs

# MODEL = 'gpt-4.1-nano'
MODEL = 'gpt-4.1-mini'

EMBEDDINGS_MODEL = 'text-embedding-ada-002'

PATH_PRODUCTS_VECTORDB = "data/data-rag-product-information/products_clean.db"

PATH_TRANSACTIONS_DATABASE = "sqlite:///data/database-sql-transactions/leads_scored.db"



# * STEP 1: MAKE SUPERVISOR AGENT 

def make_marketing_analytics_supervisor_agent(model, temperature=0):
    
    subagent_names = ["Product_Expert", "Business_Intelligence_Expert", "Marketing_Email_Writer"]
    
    # Handle case when users want to make a different model than ChatOpenAI
    if isinstance(model, str):
        llm = ChatOpenAI(model = model)
    else:
        llm = model 
        
    system_prompt = (
        """
        You are a supervisor tasked with managing a conversation between the following workers: {subagent_names}.

        Each worker has the following knowledge and skills:

            1. Product_Expert: Knows course content and can explain details from course sales pages.  
            (Do not have the Product_Expert write emails—that’s the Marketing_Email_Writer’s job.)

            2. Business_Intelligence_Expert: Knows our customer transactions database.  
            Can write SQL, produce tables and charts based on leads, purchases, and transactions data.

            3. Marketing_Email_Writer: Drafts marketing emails using Product_Expert content and  
            customer segments identified by the Business_Intelligence_Expert.

        Assignment Rules:
        • Track which worker acted last.  
        • **Never** assign the same worker twice in a row unless they explicitly request to continue.  
        • If the same expertise is needed twice, see if a different worker can handle the follow‐up (e.g., BI_Expert hands off to Product_Expert for context).  
        • When multiple workers can fulfill a request, rotate in round‐robin order to balance workload.

        Workflow:
        1. Read the user’s request.  
        2. Decide which worker is best suited **and** is not the same as the last one you chose.  
        3. Respond with exactly the worker’s name (e.g. `Business_Intelligence_Expert`) to invoke them.  
        4. That worker will perform their task and return results.  
        5. Repeat until the task is complete, then respond with `FINISH`.
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
        | llm.bind(functions=[function_def], function_call={"name": "route"})
        | JsonOutputFunctionsParser()
    )
    
    # LangGraph State Graph
    
    class GraphState(TypedDict):
        messages: Sequence[BaseMessage]
        next: str

    def supervisor_node(state):
        print("---SUPERVISOR---")
        
        messages = state.get("messages")
        
        result = supervisor_chain.invoke({"messages": messages})
        
        next_worker = result.get("next")

        return {"next": next_worker}

    workflow = StateGraph(GraphState)

    workflow.add_node("supervisor", supervisor_node)
    workflow.add_edge(START, "supervisor")
    workflow.add_edge("supervisor", END)

    app = workflow.compile()

    return app
    

supervisor_agent = make_marketing_analytics_supervisor_agent(
    model=MODEL, 
    temperature=0.7
)

supervisor_agent

# display(Image(supervisor_agent.get_graph().draw_png()))


# Test: Product Expert
messages = [
    HumanMessage("Is the 4-Course R-Track Open for Enrollment?")
]

result = supervisor_agent.invoke({"messages": messages})
result


# Test: Business Intelligence Expert

messages = [
    HumanMessage("What are the top 5 product sales revenue by product name? Make a donut chart. Use suggested price for the sales revenue and a unit quantity of 1 for all transactions.")
]

result = supervisor_agent.invoke({"messages": messages})
result


# * STEP 2: MAKE SUB-AGENTS

# Product Expert
product_expert_agent = make_product_expert_agent(
    model=MODEL, 
    model_embedding=EMBEDDINGS_MODEL, 
    db_path=PATH_PRODUCTS_VECTORDB
)

product_expert_agent

# display(Image(product_expert_agent.get_graph().draw_png()))

# Business Intelligence Agent
business_intelligence_agent = make_business_intelligence_agent(model=MODEL, db_path=PATH_TRANSACTIONS_DATABASE)

business_intelligence_agent

# display(Image(business_intelligence_agent.get_graph().draw_png()))

# Marketing Email Copy Writer
marketing_agent = make_marketing_email_writer_agent(model=MODEL)

marketing_agent

# display(Image(marketing_agent.get_graph().draw_png()))

# * STEP 3: SUPERVISOR-LED TEAM LANGGRAPH

# LANGGRAPH

class GraphState(TypedDict):
    # Team Messages State Tracking
    messages: Annotated[Sequence[BaseMessage], operator.add]
    # Supervisor State Tracking
    next: str
    # Business Intelligence Expert State Tracking
    sql_query : str
    data: dict
    chart_plotly_code: str
    chart_plotly_json: dict
    # Marketing Email Writer State Tracking
    email_list: list
    email_subject: str
    email_body: str
    

    
def supervisor_node(state):
    
    result = supervisor_agent.invoke(state)
    
    print(result.get("next"))
    
    return {'next': result.get("next")}


def product_expert_node(state):
    
    result = product_expert_agent.invoke(state)
    
    return {
        "messages": result.get("response"),
    }
    
def business_intelligence_expert_node(state):
    
    result = business_intelligence_agent.invoke(state)
    
    return {
        "messages": result.get("response"),
        # Business Intelligence Expert State Tracking
        "sql_query": result.get("sql_query"),
        "data": result.get("data"),
        "chart_plotly_code": result.get("chart_plotly_code"),
        "chart_plotly_json": result.get("chart_plotly_json"),
    }


def email_writer_node(state):
    
    result = marketing_agent.invoke(state)
    
    return {
        "messages": result.get("response"),
        # Marketing Email Writer State Tracking
        "email_list": result.get("email_list"),
        "email_subject": result.get("email_subject"),
        "email_body": result.get("email_body"),
    }

# * WORKFLOW DAG

workflow = StateGraph(GraphState)

workflow.add_node("supervisor", supervisor_node)
workflow.add_node("Product_Expert", product_expert_node)
workflow.add_node("Business_Intelligence_Expert", business_intelligence_expert_node)
workflow.add_node("Marketing_Email_Writer", email_writer_node)

workflow.set_entry_point("supervisor")

workflow.add_edge('Product_Expert', "supervisor")
workflow.add_edge('Business_Intelligence_Expert', "supervisor")
workflow.add_edge('Marketing_Email_Writer', "supervisor")

workflow.add_conditional_edges(
    "supervisor", 
    lambda state: state.get("next"), 
    {
        'Product_Expert': 'Product_Expert', 
        'Business_Intelligence_Expert': 'Business_Intelligence_Expert', 
        'Marketing_Email_Writer':'Marketing_Email_Writer',
        'FINISH': END
    }
)


# * NEW: Short Term Memory
checkpointer = MemorySaver()

app = workflow.compile(checkpointer=checkpointer)

app

# Visualize the sub-graphs 
display(Image(app.get_graph(xray=1).draw_mermaid_png()))

# display(Image(app.get_graph(xray=1).draw_png()))


# TEST: Complex request

messages = [HumanMessage(content="Find the top 20 email subscribers ranked by probability of purchase (p1 lead score in the leads_scored table) who have have not purchased any courses yet? Have the Product Expert collect information on the 5-Course R-Track for use with the Marketing Expert. Have the Marketing Expert write a compelling marketing email.")]


result = app.invoke(
    input = {"messages": messages},
    # * NEW: Add thread_id
    config = {
        "recursion_limit": 10,
        "configurable": {"thread_id": "123"}
    },
)

list(result.keys())

result["messages"]

for message in result['messages']:
    if message.name:
        pprint(message.name)
    pprint(message.content)
    
# Getting State Elements

pprint(result['sql_query'])

pd.DataFrame(result['data'])

result['email_list']
result['email_subject']
Markdown(result['email_body'])


# TEST: Persistant Short Term Memory

messages = [HumanMessage(content="Make sure to remove Kamryn Tremblay from the email list when you make the email list. Please return the results with Kamryn Tremblay removed.")]

result = app.invoke(
    input = {"messages": messages},
    config = {
        "recursion_limit": 10,
        "configurable": {"thread_id": "123"}
    },
)

result

Markdown(result['messages'][-1].content)


# * STEP 4: MODULARIZE THE APP

from marketing_analytics_team.teams import make_marketing_analytics_team

from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()

marketing_analytics_team = make_marketing_analytics_team(
    model=MODEL,
    model_embedding=EMBEDDINGS_MODEL,
    path_products_vector_db=PATH_PRODUCTS_VECTORDB,
    path_transactions_sql_db=PATH_TRANSACTIONS_DATABASE,
    checkpointer=checkpointer
)
marketing_analytics_team

# Display the sub-graphs
display(Image(marketing_analytics_team.get_graph(xray=1).draw_mermaid_png()))

# TEST: Complete team usage

messages = [HumanMessage(content="Find the top 20 email subscribers ranked by probability of purchase (p1 lead score in the leads_scored table) who have have not purchased any courses yet? Have the Product Expert collect information on the 5-Course R-Track for use with the Marketing Expert. Have the Marketing Expert write a compelling marketing email.")]


result = marketing_analytics_team.invoke(
    input = {"messages": messages},
    # * NEW: Add thread_id
    config = {
        "recursion_limit": 10,
        "configurable": {"thread_id": "123"}
    },
)
result['messages']

Markdown(result["messages"][-1].content)

Markdown(result['email_body'])

Markdown(result['email_subject'])

result['email_list']

# TEST: Persistant Short Term Memory

messages = [HumanMessage(content="Marketing Writer: Make sure to remove Kamryn Tremblay from the email list when you make the email list. Please return the results with Kamryn Tremblay removed.")]

result = marketing_analytics_team.invoke(
    input = {"messages": messages},
    # * NEW: Add thread_id
    config = {
        "recursion_limit": 10,
        "configurable": {"thread_id": "123"}
    },
)

result

result["messages"]

Markdown(result["messages"][-1].content)

pprint(result["messages"][-1].content)

pprint(result["messages"][-2].content)

result['email_list']

