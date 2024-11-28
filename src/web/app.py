from fastapi import FastAPI, Form, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()
templates = Jinja2Templates(directory="web-ui/templates")
app.mount("/static", StaticFiles(directory="web-ui/static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/search", response_class=HTMLResponse)
async def search(request: Request, query: str = Form(...)):
    # Perform your search logic here
    results = [{"id": 1, "text": "Result 1"}, {"id": 2, "text": "Result 2"}]
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "query": query, "results": results},
    )
