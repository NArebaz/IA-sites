# LocalIA — detectar comércios sem site profissional e gerar orçamentos

Este repositório contém um protótipo local em Python para:
- Buscar comércios perto de uma localização (OpenStreetMap/Overpass ou Google Places)
- Detectar se o comércio NÃO possui um site profissional (heurística)
- Gerar orçamentos (HTML e opcionalmente PDF)
- Enviar orçamentos por e‑mail (opcional, via SMTP)
- Geocoding por endereço (Google Geocode ou Nominatim como fallback)

Estrutura do repositório
- main.py                 - CLI principal
- services/               - módulos (osm, google_places, evaluator, geocode, mailer, quote)
- templates/quote_template.html
- config.yaml             - template de configuração (não inclua chaves em commits públicos)
- requirements.txt

Como começar (resumo rápido)
1) Clonar branch localia-setup ou baixar o ZIP da release/branch.
   git clone --branch localia-setup https://github.com/NArebaz/IA-sites.git
   cd IA-sites

2) Criar ambiente Python e instalar dependências (Python 3.9+ recomendado)
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt

3) Configurar config.yaml (ou usar variáveis de ambiente). Para Gmail, use App Password.

4) Execute (exemplos):
   python main.py --address "Av. Paulista, 1000, São Paulo" --radius 1500 --out quotes --preview
   python main.py --lat -23.55052 --lon -46.633308 --radius 1000 --use-google --out quotes --send-email

Notas sobre PDFs
- Ative output_pdf: true e instale dependências nativas (cairo, pango, libffi) para WeasyPrint.

Contribuições
- Este é um protótipo. Sinta-se livre para abrir issues/PRs no seu repo privado e eu posso continuar ajudando.
