import re

def slugify(form_name: str) -> str:
    slug = form_name.strip().lower()
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"[^a-z0-9\-]", "", slug)
    slug = re.sub(r"-+", "-", slug)
    slug = slug.strip("-")
    return slug

def generate_unique_slug(form_name, collection):
    #TODO: Implement unique naming for the form slugs if repeated names encountered. Not required for now.
    pass
    