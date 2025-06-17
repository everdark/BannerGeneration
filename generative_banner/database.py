"""Database connection singleton."""

from google.cloud import firestore

from generative_banner.config import settings

db = firestore.Client(project=settings.gcp_project, database=settings.firestore_id)
