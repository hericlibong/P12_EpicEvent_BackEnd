from models.contract import Contract
from .base_dao import BaseDAO

class ContractDAO(BaseDAO):

    def create_contract(self, contract_data):
        """
        Créer un contrat avec les données fournies.
        """
        contract = Contract(**contract_data)
        self.session.add(contract)
        self.session.commit()
        self.session.refresh(contract)
        return contract
    
    def get_contract_by_id(self, contract_id: int):
        """
        Récupère un contrat par son identifiant.
        """
        return self.session.query(Contract).filter_by(Contract.id==contract_id).first()
    
    def get_all_contracts(self):
        """
        Récupère tous les contrats.
        """
        return self.session.query(Contract).all()
    
    def update_contract(self, contract_id: int, contract_data: dict):
        """
        Met à jour un contrat avec les données fournies.
        """
        contract = self.get_contract_by_id(contract_id)
        if not contract:
            return None
        for key, value in contract_data.items():
            setattr(contract, key, value)
        self.session.commit()
        self.session.refresh(contract)
        return contract
    
    def delete_contract(self, contract_id: int):
        """
        Supprime un contrat par son identifiant.
        """
        contract = self.get_contract_by_id(contract_id)
        if not contract:
            return False
        self.session.delete(contract)
        self.session.commit()
        return True