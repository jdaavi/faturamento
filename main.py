from fastapi import FastAPI, File, UploadFile, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import pandas as pd
import os
from datetime import datetime, timedelta

app = FastAPI()
templates = Jinja2Templates(directory="templates")

UPLOAD_DIR = 'arquivos'
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def upload_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": Request})

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    df = pd.read_excel(file_path)

    df.columns = [col.strip().lower() for col in df.columns]

    col_entrega = 'previsão entrega'
    if col_entrega.lower() in df.columns:
        df = df[df[col_entrega.lower()] != '######']

    if 'DhVenda' in df.columns:
      df['DhVenda'] = pd.to_datetime(df['DhVenda'], errors='coerce')

    ontem = datetime.now().date() - timedelta(days=1)

    # Filtra apenas as linhas com Dhvenda igual a ontem
    df = df[df['DhVenda'].dt.date == ontem]

    if 'Origem Pedido' in df.columns:
        def map_venda2(origem):
            if origem == "Ifood":
                return "Ifood"
            elif origem == "AnotaAi":
                return "Central de Atendimento"
            else:
                return None
        
        df['venda2'] = df['Origem Pedido'].apply(map_venda2)

    def tratar_local(row):
            telefone = str(row.get('Telefone')).strip() if pd.notna(row.get('Telefone')) else ""

            if telefone.startswith("100"):
                return "Alimentação de Funcionáro"
            
            if telefone.startswith("101") or telefone == '':
                return "Venda Balcão"
            
            if telefone.startswith("102"):
                return "Teste"
            
            if telefone.startswith("103"):
                return "Serviço"
            
            if telefone.startswith("104"):
                return "Segunda Taxa"

            if telefone.startswith("105"):
                return "Segunda Taxa"
            
            if telefone.startswith("106"):
                return "Segunda Taxa"
       
            mascara_local = df['Origem Pedido'] == "Local"
            df.loc[mascara_local, 'venda2'] = df[mascara_local].apply(tratar_local, axis=1)