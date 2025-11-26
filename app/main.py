if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    from app.core.product_sync import sync_products

    load_dotenv()

    token = os.getenv("XBZ_TOKEN")
    cnpj = os.getenv("XBZ_CNPJ")
    omie_app_key = os.getenv("OMIE_APP_KEY")
    omie_app_secret = os.getenv("OMIE_APP_SECRET")

    sync_products(
        token=token,
        cnpj=cnpj,
        omie_app_key=omie_app_key,
        omie_app_secret=omie_app_secret,
        dry_run=False,       # <--- Now it's a real sync
        preview_count=None      # <--- Just one product for safety
    )
