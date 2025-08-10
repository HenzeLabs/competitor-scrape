import argparse
from .runner import run_all

def main():
    parser = argparse.ArgumentParser(description="Competitor scraper CLI")
    subparsers = parser.add_subparsers(dest="command")

    scrape_parser = subparsers.add_parser("scrape", help="Scrape all configured sites")
    scrape_parser.add_argument("--site", default="all", help="Site name or 'all'")

    args = parser.parse_args()

    if args.command == "scrape":
        run_all()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
