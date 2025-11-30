import re

class SlugCreator:
    def __init__(self, forms_db):
        self.forms_db = forms_db

    def _slugify(self, form_name: str) -> str:
        
        slug = form_name.strip().lower()
        slug = re.sub(r"\s+", "-", slug)
        slug = re.sub(r"[^a-z0-9\-]", "", slug)
        slug = re.sub(r"-+", "-", slug)
        slug = slug.strip("-")
        return slug

    def generate_unique_slug(self, form_name):

        main_slug = self._slugify(form_name)

        if not self.forms_db.find_document({"form_slug": main_slug}):
            return main_slug
        suffix = 1
        while True:
            new_slug = f"{main_slug}-{suffix}"
            if not self.forms_db.find_document({"form_slug": new_slug}):
                return new_slug
            suffix += 1