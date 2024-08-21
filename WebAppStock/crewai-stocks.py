#Instalação das libs
#!pip install yfinance==0.2.41
#!pip install crewai==0.28.8
#!pip install 'crewai[tools]'
#!pip install langchain==0.1.20
#!pip install langchain-openai==0.1.7
#!pip  install langchain-community==0.0.38
#!pip install duckduckgo-search==5.3.0
#!pip install streamlit

#import das libs
import json
import os
from datetime import datetime

import yfinance as yf

from crewai import Agent, Task, Crew, Process

from langchain.tools import Tool
from langchain_openai import ChatOpenAI
from langchain_community.tools import DuckDuckGoSearchResults

import streamlit as st

#from IPython.display import Markdown

#Criando Yahoo Finance Tool
def fetch_stock_price(ticket):
    stock = yf.download(ticket, start="2023-08-08", end="2024-08-08")
    return stock

yahoo_finance_tool = Tool(
    name = "Yahoo Finance Tool",
    description = "Fetches stocks prices for {ticket} from the last year about a especific stock from Yahoo Finance API",
    func = lambda ticket: fetch_stock_price(ticket)
)

#importando OPENIA - LLM GPT
os.eviron['OPENA_API_KEY'] = st.secrets['OPENA_API_KEY']
llm = ChatOpenAI(model="gpt-3.5-turbo")


stockPriceAnalyst = Agent (
    role = "Senior Stock price Analyst",
    goal = "find the {ticket} stock price and analyses trends",
    backstory = """ You are highly experienced in analyzing the price of an specific stock and
    make predctions about its future price.""" ,
    verbose = True,
    llm= llm,
    max_iter = 5,
    memory = True,
    tools=[yahoo_finance_tool],
    allow_delegation = False
)

getStockPrice = Task(
    description= "Analyze the stock {ticket} price history and create a trend analyses of up, down or sideways",
    expected_output = """ Specifythe current trend stock price - up,  down, or sideways. eg. stock = 'APPL, price UP' """,
    agent= stockPriceAnalyst
)

# Importando a tool de search
search_tool = DuckDuckGoSearchResults(backend = 'news', num_results=10)

newsAnalyst = Agent(
    role = "Stock News Analyst",
    goal = """Create a short summary of the market  news related to the  stock {ticket} company. Specify the current trend - up, down, or sideways with
    the news context. For each stock asset, specify a number between 0 and 100, where 0 is extreme fear and 100 is extreme good.""",
    backstory = """ You're higly experienced in analyzing the market  trends and news and have tracked assets for more then 10 years.
    
    You're also master level analyts in the tradicional markets and have deep understading of human psychology. 

    You understand news, theirs tittles and information, but you look at those with a health dose of skepcism. You consider also the source of news articles. 
    """ ,
    verbose = True,
    llm= llm,
    max_iter = 10,
    memory = True,
    tools=[yahoo_finance_tool],
    allow_delegation = False
)

get_news = Task(
    description= f"""Take the stock and always include BTC to it (if not request)
    use the search tool to search each one individually.
    
    The  current date is {datetime.now()}.
    
    Compose the results into a helpfull report""",
    expected_output = """ A summary of the  overeall market and one sentence summary for each request asset.
     Include  a fear/greed  score for  each asset based on the  news. Use format:
      <STOCK ASSET>
      <SUMMAY BASED ON NEWS>
      <TREND PREDICTION>
      <FEAR/GREED SCORE> """,
    agent= stockPriceAnalyst
)


stockAnalystWrite = Agent(
    role = "Senior Stock Analyts Writer"
    goal= "Analyze the trends price and news and write an insighfull compelling and informative 3 paragraph long newsletter based on the stock" 
    backstory= """You re widely accepted as the best stock analyst in the market. You understand complex concepts and create compelling storles and narratives that resonate with wider audiences.
    You understand macro factors and combine multiple theories - eg. cycle theory and fundamental anatyses.
    You re able to hold multiple opinions when analyzing anything.""",

    verbose = True,
    llm=,
    max_iter = 5,
    memory=True,
    allow_delegation = True
)

writeAnalyses = Task(
    description = """ Use the stock price trend and the stock news report to create an analyses and write the newsletter about the {ticket} company
that is brief and highlights the most important points.
Focus on the stock price trend, news and fear/greed score. What are the  near future considerations?
Include the previous analyses of stock trend and news summary.
""",
    expected_output= """ An eloquent 3 paragraphs newsletter formated as markdown in an easy readable manner. It should contain:
    - 3 bullets executive summary
    - Introduction - set the overall picture and spike up the interest
    - main part provides the meat of the analysis including the news sumnary and fead/greed scores
    - summary - key facts and concrete future trend prediction - up, down or sideways.
""",
    agent = stockAnalystWrite,
    context = [getStockPrice, get_news]

)

crew = Crew(
    agents = [stockPriceAnalyst, newsAnalyst, stockAnalystWrite],
    tasks = [getStockPrice, get_news, writeAnalyses],
    verbose = 2,
    process = Process.hierarchical ,
    full_output = True,
    share_crew = False,
    manager_llm=llm,
    max_iter = 15
)

#results = crew.kickoff(inputs={'ticket' : 'AAPL'})

results['final_output']

with st.sidebar:
    st.header('Enter the Stock to Research stock')

    with st.form(key='research_form'):
        topic = st.text_input("select the ticket")
        submit_button = st.form_submit_button(label = "Run Research")

if submit_button:
    if not topic:
        st.error("Please fill the ticket field")
    else:
        results = crew.kickoff(inputs={'ticket' : topic})

        st.subheader("Results of your  research:")
        st.write(results ['final_output'])


#streamlit run crewai-stocks.py