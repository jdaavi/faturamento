import requests
from geopy.distance import geodesic
import numpy as np
import psycopg2
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

def conectar_banco():
    try:
        conexao = psycopg2.connect (
            host = 'datalake_menu.postgresql.dbaas.com.br',
            database = 'datalake_menu',
            user = 'datalake_menu',
            password = 'Acesso1!'
        )
        return conexao
    except Exception as e:
        print(f'Erro ao conectar ao banco: {e}')
        return None

def obter_distancia_banco(endereco1, endereco2):
    conexao = conectar_banco()
    if conexao:
        try:
            cursor = conexao.cursor()
            query = """SELECT distancia FROM distancias WHERE endereco1 = %s AND endereco2 = %s"""
            cursor.execute(query, (endereco1, endereco2))
            resultado = cursor.fetchone()
            if resultado:
                return resultado[0]
            else:
                return  None
        except Exception as e:
            print(f'Erro ao consultar o banco: {e}')
            return None
        finally:
            conexao.close()

def registrar_distancia_banco(endereco1, endereco2, distancia):
    conexao = conectar_banco()
    if conexao:
        try:
            cursor = conexao.cursor()
            query = """INSERT INTO distancias (endereco1, endereco2, distancia) VALUES (%s, %s, %s)"""
            cursor.execute(query, (endereco1, endereco2, distancia))
            conexao.commit()
        except Exception as e:
            print(f"Erro ao registrar no banco: {e}")
        finally:
            conexao.close()
            
def obter_coordenadas(endereco):
    url = f"https://nominatim.openstreetmap.org/search?q={endereco}&format=json"
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    dados = response.json()
    
    if dados:
        return float(dados[0]['lat']), float(dados[0]['lon'])
    else:
        return None

def calcular_distancia(endereco1, endereco2):
    coordenadas1 = obter_coordenadas(endereco1)
    coordenadas2 = obter_coordenadas(endereco2)
    
    if coordenadas1 is None or coordenadas2 is None:
        print("Não foi possível obter as coordenadas.")
        return None
    
    distancia = geodesic(coordenadas1, coordenadas2).kilometers
    return np.round(distancia,2)

def classificar_area(distancia):
    areas_de_entrega = {
        "A": (0, 0.99),
        "B": (1, 1.99),
        "C": (2, 2.99),
        "D": (3, 3.99),
        "E": (4, 4.99),
        "F": (5, 5.99),
        "G": (6, 6.99),
        "H": (7, 7.99),
        "I": (8, 8.99),
        "J": (9, 9.99),
        "K": (10, 10.99),
    }
    
    for area, (min_km, max_km) in areas_de_entrega.items():
        if min_km <= distancia < max_km:
            return area
    
    return "Fora da área de entrega"

def calcular(endereco1, endereco2):


    distancia = obter_distancia_banco(endereco1, endereco2)
    
    if distancia is None:
        distancia = calcular_distancia(endereco1, endereco2)
        if distancia is not None:
            registrar_distancia_banco(endereco1, endereco2, distancia)
        else:
           return None, "Não foi possível calcular a distância."
    area = classificar_area(distancia)
    return distancia, area

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        endereco1 = request.form["partida"]
        endereco2 = request.form["chegada"]

        distancia, area_ou_erro = calcular(endereco1, endereco2)

        if distancia is None:
            return render_template("index.html", erro=area_ou_erro)
        
        return render_template("index.html", distancia=distancia, area=area_ou_erro)
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)

