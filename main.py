"""LocalIA - CLI principal (refatorado)
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import yaml

from services.osm import find_businesses_osm
from services.google_places import find_businesses_google
from services.evaluator import WebsiteEvaluator
from services.quote import QuoteRenderer
from services.mailer import Mailer
from services.geocode import geocode_address

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("localia")


def load_config(path: str = "config.yaml") -> Dict[str, Any]:
    if not os.path.exists(path):
        logger.warning("Config file %s not found, using defaults and environment variables.", path)
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def process_business(
    business: Dict[str, Any],
    evaluator: WebsiteEvaluator,
    renderer: QuoteRenderer,
    out_dir: str,
    pricing: Dict[str, Any],
    company: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    website = business.get("website")
    if evaluator.is_professional(website):
        logger.debug("%s: possui site profissional (%s)", business.get("name"), website)
        return None
    safe_name = (business.get("name") or "business").replace(" ", "_")
    fname = f"{safe_name}_{business.get('id','')}.html"
    outpath = os.path.join(out_dir, fname)
    renderer.render(business, outpath, pricing, company)
    return {
        "name": business.get("name"),
        "address": business.get("address", ""),
        "phone": business.get("phone", ""),
        "email": business.get("email", ""),
        "website_tag": website or "",
        "quote_file": outpath,
    }


def write_csv(rows: Iterable[Dict[str, Any]], path: str) -> None:
    import csv

    rows = list(rows)
    if not rows:
        logger.info("Nenhum orçamento gerado; CSV não criado.")
        return
    keys = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def cli(argv: Optional[List[str]] = None) -> int:
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
    args = p.parse_args(argv)

    cfg = load_config(args.config)
    pricing = cfg.get("pricing", {
        "package_name": "Site Profissional Básico",
        "price": "R$ 1.800,00",
        "features": [
            "Site responsivo (até 5 páginas)",
            "Formulário de contato e mapa",
            "SEO básico",
            "Hospedagem por 1 ano (opcional)",
        ],
    })
    company = cfg.get("company", {})

    lat = args.lat
    lon = args.lon
    if args.address and (lat is None or lon is None):
        api_key = cfg.get("google_geocode_api_key") or cfg.get("google_places_api_key")
        logger.info("Geocoding address: %s", args.address)
        loc = geocode_address(args.address, api_key=api_key)
        if not loc:
            logger.error("Falha ao geocodificar o endereço fornecido.")
            return 2
        lat, lon = loc
        logger.info("Endereço geocodificado: lat=%s lon=%s", lat, lon)

    if lat is None or lon is None:
        logger.error("Latitude/longitude não fornecidas. Use --lat/--lon ou --address para geocodificação.")
        return 2

    os.makedirs(args.out, exist_ok=True)

    if args.use_google:
        api_key = cfg.get("google_places_api_key")
        if not api_key:
            logger.error("Google Places solicitado, mas google_places_api_key ausente em %s", args.config)
            return 2
        businesses = find_businesses_google(lat, lon, args.radius, api_key)
    else:
        businesses = find_businesses_osm(lat, lon, args.radius)

    logger.info("Encontrados %d candidatos", len(businesses))

    evaluator = WebsiteEvaluator(cfg.get("evaluator", {}))
    renderer = QuoteRenderer(template_path="templates/quote_template.html", pdf=cfg.get("output_pdf", False))

    mailer: Optional[Mailer] = None
    if args.send_email:
        smtp_cfg = cfg.get("smtp", {})
        mailer = Mailer(smtp_cfg)

    rows: List[Dict[str, Any]] = []
    from concurrent.futures import ThreadPoolExecutor, as_completed

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(process_business, b, evaluator, renderer, args.out, pricing, company): b for b in businesses}
        for fut in as_completed(futures):
            b = futures[fut]
            try:
                res = fut.result()
                if res:
                    rows.append(res)
                    if args.send_email and res.get("email") and mailer:
                        try:
                            html_path = res.get("quote_file")
                            pdf_path = None
                            if cfg.get("output_pdf", False):
                                pdf_path = html_path.rsplit('.', 1)[0] + '.pdf'
                            with open(html_path, 'r', encoding='utf-8') as fh:
                                html_body = fh.read()
                            subject = f"Orçamento - {res.get('name')} - {company.get('name','')}"
                            mailer.send_quote(res.get('email'), subject, html_body, attachment_path=pdf_path)
                        except Exception:
                            logger.exception("Falha ao enviar e-mail para %s", res.get('email'))
            except Exception:
                logger.exception("Erro processando %s", b.get('name'))

    csv_path = os.path.join(args.out, "results.csv")
    write_csv(rows, csv_path)
    logger.info("Gerados %d orçamentos. CSV: %s", len(rows), csv_path)

    if args.preview:
        for r in rows[:50]:
            print(f"- {r['name']} | {r['address']} | {r['phone']} | {r['email']} -> {r['quote_file']}")

    return 0


if __name__ == "__main__":
    sys.exit(cli())
