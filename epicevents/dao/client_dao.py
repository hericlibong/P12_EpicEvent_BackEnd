from models.client import Client
from .base_dao import BaseDAO
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError
from psycopg2.errors import UniqueViolation
import sqlite3

class ClientDAO(BaseDAO):

    def create_client(self, client_data):
        """
        Crée un client avec les données fournies.
        """
        client = Client(**client_data)
        self.session.add(client)
        try:
            self.session.commit()

            # Recharger le client avec les relations nécessaires
            client = self.session.query(Client).options(
                joinedload(Client.sales_contact),
                # Ajoutez d'autres relations que vous souhaitez charger
            ).filter_by(id=client.id).one()

            # Détacher l'objet de la session
            self.session.expunge(client)


            return client
        
        except IntegrityError as e:
            self.session.rollback()

            # Gérer SQLite pour faciliter les tests
            if isinstance(e.orig, sqlite3.IntegrityError) and "UNIQUE constraint failed" in str(e.orig):
                raise ValueError("Adresse email déjà utilisée.") from e

            # Gérer PostgreSQL
            if isinstance(e.orig, UniqueViolation):
                constraint_name = getattr(e.orig.diag, 'constraint_name', None)
                if constraint_name == 'ix_clients_email':
                    raise ValueError("Adresse email déjà utilisée.") from e
                else:
                    raise ValueError("Erreur de contrainte unique non gérée.") from e

            # Exception générique pour les autres cas
            raise Exception("Erreur d'intégrité non gérée.") from e

   
    def get_client_by_id(self, client_id: int):
        """
        Récupère un client par son identifiant.
        """
        return self.session.query(Client).filter_by(id=client_id).first()
    
    def get_all_clients(self):
        """
        Récupère tous les clients.
        """
        return self.session.query(Client).all()
    
    def update_client(self, client_id: int, client_data: dict):
        """
        Met à jour un client avec les données fournies.
        """
        client = self.get_client_by_id(client_id)
        if not client:
            return None
        for key, value in client_data.items():
            setattr(client, key, value)
        self.session.commit()
        self.session.refresh(client)
        return client
    
    def get_clients_by_sales_contact(self, sales_contact_id: int):
        """
        Récupère tous les clients d'un contact commercial.
        """
        return self.session.query(Client).filter_by(sales_contact_id=sales_contact_id).all()
    
    def delete_client(self, client_id: int):
        """
        Supprime un client par son identifiant.
        """
        client = self.get_client_by_id(client_id)
        if not client:
            return False
        self.session.delete(client)
        self.session.commit()
        return True
