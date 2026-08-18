LocalIA - detectar comércios sem site profissional e gerar orçamentos
-----------------------------------------------------------------

Instalação:
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt

Uso:
  python main.py --lat <LAT> --lon <LON> --radius 1000 --out quotes --preview
  Para usar Google Places:
    - preencha google_places_api_key em config.yaml
    - execute com --use-google

Observações:
  - Para gerar PDFs ative output_pdf: true e instale dependências do WeasyPrint no SO.
