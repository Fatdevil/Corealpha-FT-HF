from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import health, summarize, sentiment, agent, vote

app = FastAPI(title='CoreAlpha Adapter API (v1.1)', version='0.1.1', docs_url='/', description='DI‑vänligt adapter‑API för FinGPT + Agents + VotingEngine.')
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'], allow_credentials=True)
app.include_router(health.router, tags=['health'])
app.include_router(summarize.router, tags=['summarize'])
app.include_router(sentiment.router, tags=['sentiment'])
app.include_router(agent.router, tags=['agent'])
app.include_router(vote.router, tags=['vote'])
