from langchain.agents import create_agent
from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from tool import web_search , scrape_url
from dotenv import load_dotenv
import os
import requests

load_dotenv()

llm = ChatMistralAI(model= "mistral-small-latest" , temperature = 0) 

def build_search_agent():
    return create_agent(
        model=llm ,
        tools=[web_search]
    )

def build_reader_agent():
    return create_agent(
        model=llm ,
        tools=[scrape_url]
    )

writer_prompt= ChatPromptTemplate.from_messages([
    ('system' , "you are an expert research writer . write clearer , structred and insightful reports"),
    ('human' , """write a detailed research report on the topic below
Topic : {topic}

research gathered: {research}

structre report as:
     --introduction
     --key findings
     --conclusiuon
     --Sources(list of all urls found in the research)

be deatailed and factual     
     """)
])




writer_runnable = writer_prompt | llm | StrOutputParser()





critic_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an expert Research Critic Agent.Your job is to review research reports produced by other AI agents "
        ),
        (
            "human",
            """
        Review the following research report and provide detailed feedback.
        Provide:
        Evaluate the report on:

        1. Accuracy and factual consistency
        2. Completeness of information
        3. Logical structure and organization
        4. Clarity and readability
        5. Use of evidence and supporting details
        6. Missing topics or weak sections
        7. Overall quality score (1-10)



        Be objective, detailed, and constructive.

        Score: X/10
        - Strengths
        - Weaknesses
        - Specific improvements
        - Final Score
        Research Report:
        {report}
        """
        )
    ]
) 


critic_runnable = critic_prompt | llm | StrOutputParser()