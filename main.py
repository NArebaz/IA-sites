#!/usr/bin/env python3
"""
main.py - CLI entrypoint (updated with address geocoding)
"""
import argparse
import logging
import os
import yaml
from services.osm import find_businesses_osm
from services.google_places import find_businesses_google
from services.evaluator import WebsiteEvaluator
from services.quote import QuoteRenderer
from services.mailer import Mailer
from services.geocode import geocode_address
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("localia")


def load_config(path="config.yaml"):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def process_business(business, evaluator, renderer, out_dir, pricing, company):
    website = business.get("website")
    has_prof = evaluator.is_professional(website)
    if has_prof:
        logger.debug("%s: tem site profissional (%s)", business.get("name"), website)
        return None
    fname = f"{business.get('name','business')}_{business.get('id','')}.html".replace(" ", "_")
    outpath = os.path.join(out_dir, fname)
    renderer.render(business, outpath, pricing, company)
    return {
        "name": business.get("name"),
        "address": business.get("address", ""),
        "phone": business.get("phone", ""),
        "email": business.get("email", ""),
        "website_tag": website or "",
        "quote_file": outpath
    }


def write_csv(rows, path):
    if not rows:
        return
    keys = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def cli():
    p = argparse.ArgumentParser(description="LocalIA - detectar comércios sem site profissional e gerar orçamentos")
    p.add_argument("--lat", type=float, help="Latitude do centro de busca")
    p.add_argument("--lon", type=float, help="Longitude do centro de busca")
    p.add_argument("--address", type=str, help="Endereço para geocodificação (ex: 'R. Exemplo, 123, São Paulo')")
    p.add_argument("--radius", type=int, default=1000, help="Raio em metros")
    p.add_argument("--out", default="quotes", help="Diretório de saída")
    p.add_argument("--use-google", action="store_true", help="Usar Google Places (requer config.yaml with key)")
    p.add_argument("--workers", type=int, default=8, help="Número de threads para checagens")
    p.add_argument("--preview", action="store_true", help="Somente listar resultados (não enviar e-mail)")
    p.add_argument("--send-email", action="store_true", help="Enviar orçamentos por e-mail quando o estabelecimento tiver email")
    p.add_argument("--config", default="config.yaml", help="Caminho para config.yaml")
    args = p.parse_args()

    cfg = load_config(args.config)
    pricing = cfg.get("pricing", {
        "package_name": "Site Profissional Básico",
        "price": "R$ 1.800,00",
        "features": [
            "Site responsivo (até 5 páginas)",
            "Formulário de contato e mapa",
            "SEO básico",
            "Hospedagem por 1 ano (opcional)"
        ]
    })
    company = cfg.get("company", {"name": "Sua Empresa", "contact_email": "contato@seudominio.com", "contact_phone": "+55 11 9XXXX-XXXX"})

    # If address provided, geocode it (Google Geocode API if configured, otherwise Nominatim)
    lat = args.lat
    lon = args.lon
    if args.address and (lat is None or lon is None):
        api_key = cfg.get("google_geocode_api_key") or cfg.get("google_places_api_key")
        logger.info("Geocoding address: %s", args.address)
        res = geocode_address(args.address, api_key=api_key)
        if not res:
            logger.error("Não foi possível geocodificar o endereço fornecido. Saindo.")
            return
        lat, lon = res
        logger.info("Endereço geocodificado: lat=%s lon=%s", lat, lon)

    if lat is None or lon is None:
        logger.error("Latitude/longitude não fornecidas. Use --lat/--lon ou --address para geocodificação.")
        return

    Path(args.out).mkdir(parents=True, exist_ok=True)

    if args.use_google:
        api_key = cfg.get("google_places_api_key")
        if not api_key:
            logger.error("Google Places solicitado, mas google_places_api_key ausente em %s", args.config)
            return
        businesses = find_businesses_google(lat, lon, args.radius, api_key)
    else:
        businesses = find_businesses_osm(lat, lon, args.radius)

    logger.info("Encontrados %d candidatos", len(businesses))

    evaluator = WebsiteEvaluator(cfg.get("evaluator", {}))
    renderer = QuoteRenderer(template_path="templates/quote_template.html", pdf=cfg.get("output_pdf", False))

    mailer = None
    if args.send_email:
        smtp_cfg = cfg.get("smtp", {})
        mailer = Mailer(smtp_cfg)

    rows = []
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(process_business, b, evaluator, renderer, args.out, pricing, company): b for b in businesses}
        for fut in as_completed(futures):
            try:
                res = fut.result()
                if res:
                    rows.append(res)
                    # if enabled and has email, send
                    if args.send_email and res.get("email"):
                        try:
                            html_path = res.get("quote_file")
                            pdf_path = None
                            if cfg.get("output_pdf", False):
                                pdf_path = html_path.rsplit('.',1)[0] + '.pdf'
                            with open(html_path, 'r', encoding='utf-8') as fh:
                                html_body = fh.read()
                            subject = f"Orçamento - {res.get('name')} - {company.get('name')}"
                            mailer.send_quote(res.get('email'), subject, html_body, attachment_path=pdf_path)
                        except Exception as e:
                            logger.exception("Erro enviando e-mail para %s: %s", res.get('email'), e)
            except Exception as e:
                logger.exception("Erro processando %s: %s", futures[fut].get("name"), e)

    csv_path = os.path.join(args.out, "results.csv")
    write_csv(rows, csv_path)
    logger.info("Gerados %d orçamentos. CSV: %s", len(rows), csv_path)

    if args.preview:
        for r in rows[:20]:
            print(f"- {r['name']} | {r['address']} | {r['phone']} | {r['email']} -> {r['quote_file']}")

if __name__ == "__main__":
    cli()
