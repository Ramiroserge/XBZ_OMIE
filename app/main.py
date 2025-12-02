if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    from app.core.product_sync import sync_products

    load_dotenv()

    token = os.getenv("XBZ_TOKEN")
    cnpj = os.getenv("XBZ_CNPJ")
    omie_app_key = os.getenv("OMIE_APP_KEY")
    omie_app_secret = os.getenv("OMIE_APP_SECRET")
    
    # Optional: override the default max inserts per run via environment variable
    max_inserts = os.getenv("MAX_INSERTS_PER_RUN")
    if max_inserts:
        max_inserts = int(max_inserts)

    sync_products(
        token=token,
        cnpj=cnpj,
        omie_app_key=omie_app_key,
        omie_app_secret=omie_app_secret,
        dry_run=False,
        preview_count=None,
        max_inserts=max_inserts  # Uses default (500) if not set
    )
