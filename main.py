from fastapi import FastAPI
from Auth.routes import auth_router
from Quiz.routes import quiz_router
from Admin.routes import admin_router
from Domain.routes import domain_router
from Reports.routes import report_router
from Learning.routes import learning_router
from Response.routes import response_router
from Feedback.routes import conclusion_router
from Dashboard.routes import dashboard_router
from fastapi.middleware.cors import CORSMiddleware

# INIT FASTAPI
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# INCLUDE ALL ROUTERS HERE
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(quiz_router, prefix="/quiz", tags=["Quiz"])
app.include_router(admin_router, prefix="/admin", tags=["Admin"])
app.include_router(domain_router, prefix="/domain", tags=["Domain"])
app.include_router(report_router, prefix="/report", tags=["Report"])
app.include_router(learning_router, prefix="/learning", tags=["Learning"])
app.include_router(response_router, prefix="/response", tags=["Response"])
app.include_router(conclusion_router, prefix="/feedback", tags=["Feedback"])
app.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])