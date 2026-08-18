LocalIA - detectar comércios sem site profissional e gerar orçamentos
-----------------------------------------------------------------

Instalação:
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt

Configuração (config.yaml):
  - Se for usar Google Places, coloque sua chave em google_places_api_key.
  - Para geocoding por endereço com Google, coloque google_geocode_api_key (opcional). Se não informado, o sistema usa Nominatim (OpenStreetMap).
  - Para envio por SMTP, configure a seção smtp (host, port, username, password, use_tls, from_email).
  - Atualize os dados da sua empresa em 'company' (name, contact_email, contact_phone).

Uso básico (OSM - gratuito):
  python main.py --lat <LAT> --lon <LON> --radius 1000 --out quotes --preview

Geocoding por endereço (exemplo):
  python main.py --address "R. Exemplo, 123, São Paulo" --radius 1000 --out quotes --preview
  (o script tentará geocodificar o endereço usando google_geocode_api_key se configurado, caso contrário usa Nominatim)

Usando Google Places (melhor cobertura, pode ser cobrado):
  - Defina google_places_api_key em config.yaml
  python main.py --lat <LAT> --lon <LON> --radius 1000 --use-google --out quotes --preview

Gerar PDFs automaticamente:
  - Ative output_pdf: true em config.yaml e instale dependências do WeasyPrint no sistema.

Enviar orçamentos por e-mail automaticamente:
  - Preencha a seção smtp em config.yaml (ou use variáveis de ambiente se preferir evitar senhas no arquivo).
  - Execute com --send-email (os orçamentos serão enviados para os estabelecimentos que tiverem e-mail disponível).

Exemplo completo:
  python main.py --address "Av. Paulista, 1000, São Paulo" --radius 1500 --use-google --out quotes --send-email

Observações:
  - O script NÃO inclui chaves ou senhas no repositório por segurança.
  - Se quiser testar envio com Gmail, crie uma App Password (contas com 2FA) e use smtp.gmail.com:587.
