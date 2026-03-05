from fastapi import FastAPI
from Auth.routes import auth_router
from Domain.routes import domain_router
from Response.routes import response_router
from Feedback.routes import conclusion_router
from fastapi.middleware.cors import CORSMiddleware

# INIT FASTAPI
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# INCLUDE ALL ROUTERS HERE
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(domain_router, prefix="/domain", tags=["Domain"])
app.include_router(response_router, prefix="/response", tags=["Response"])
app.include_router(conclusion_router, prefix="/feedback", tags=["Feedback"])