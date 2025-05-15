from flask import Flask, request, jsonify, send_from_directory, render_template
import pandas as pd
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route('/')
def inicio():
    return render_template('tela1.html')


@app.route('/processar', methods=['POST'])
def processar():
    try:
        file = request.files['file']
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        df = pd.read_excel(filepath)
        df.columns = [col.strip().lower() for col in df.columns]

        colunas = df.columns.tolist()
        colunas_corrigidas = []
        vistas = {}
        for col in colunas:
            if col in vistas:
                colunas_corrigidas.append(f"{col}2")
            else:
                colunas_corrigidas.append(col)
                vistas[col] = True
        df.columns = colunas_corrigidas

        df.fillna({'telefone2': '101'}, inplace=True)

        if 'previsão entrega' in df.columns:
            df = df[df['previsão entrega'] != '######']

        if 'origem pedido' in df.columns:
            def map_venda2(origem):
                if origem == "Ifood":
                    return "Ifood"
                elif origem == "AnotaAi":
                    return "Central de Atendimento"
                return None

            df['venda2'] = df['origem pedido'].apply(map_venda2)

        if 'telefone2' in df.columns and 'origem pedido' in df.columns:
            def tratar_local(row):
                telefone = str(row.get('telefone2', '')).strip()
                if telefone == "":
                    return "Venda Balcão"
                elif telefone.startswith("100"):
                    return "Alimentação de Funcionáro"
                elif telefone.startswith("101"):
                    return "Venda Balcão"
                elif telefone.startswith("102"):
                    return "Teste"
                elif telefone.startswith("103"):
                    return "Serviço"
                elif telefone.startswith(("104", "105", "106")):
                    return "Segunda Taxa"
                return "Divergente"

            mascara_local = df['origem pedido'] == "Local"
            df.loc[mascara_local, 'venda2'] = df[mascara_local].apply(tratar_local, axis=1)

        nome_saida = "arquivo_corrigido.xlsx"
        caminho_saida = os.path.join(OUTPUT_FOLDER, nome_saida)
        df.to_excel(caminho_saida, index=False)

        html_preview = df.head(20).to_html(index=False)

        return jsonify({
            "success": True,
            "message": "Arquivo processado com sucesso!",
            "html": html_preview,
            "download_link": f"/download/{nome_saida}"
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True)

if _name_ == '_main_':
    app.run(debug=True)