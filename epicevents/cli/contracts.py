# cli/contracts.py
import click
from rich.console import Console
from rich.table import Table
from controllers.contract_controller import ContractController
from utils.decorators import require_permission
from click_aliases import ClickAliasedGroup
from utils.logger import get_logger, log_info, log_error


logger = get_logger('contracts')


@click.group(cls=ClickAliasedGroup)
def contracts():
    """Commandes pour gérer les contrats."""
    pass


@contracts.command()
@require_permission('can_create_contracts')
def create(user_data):
    """
    Créer un nouveau contrat
    """
    # Collecte des informations du contrat
    client_id = click.prompt('ID du client', type=int)
    amount = click.prompt('Montant total', type=float)
    remaining_amount = click.prompt('Montant restant', type=float)
    status = click.prompt('Statut (1 pour signé, 0 pour en attente)', type=int)

    contract_data = {
        'client_id': client_id,
        'amount': amount,
        'remaining_amount': remaining_amount,
        'status': bool(status),
    }

    # Créer le contrat via le contrôleur
    contract_controller = ContractController()

    try:
        contract = contract_controller.create_contract(contract_data)
        contract_controller.close()

        if contract:
            # Journalisation du contrat créé
            log_info(
                logger,
                f"Contrat créé avec succès : ID {contract.id} commercial: {contract.sales_contact.fullname}"
                )
            console = Console()
            table = Table(title="Contrat créé avec succès", show_header=False)
            table.add_column("champ", style="bold cyan")
            table.add_column("valeur", style="bold magenta")
            table.add_row("ID", str(contract.id))
            table.add_row("Client", contract.client.fullname)
            table.add_row("Montant total", str(contract.amount))
            table.add_row("Montant restant", str(contract.remaining_amount))
            table.add_row("Commercial", contract.sales_contact.fullname)
            console.print(table)
        else:
            click.echo("Erreur lors de la création du contrat.")
    except ValueError:
        click.echo("Erreur lors de la création du contrat.")
        contract_controller.close()


@contracts.command(name='update')
@require_permission('can_modify_all_contracts', 'can_modify_own_contracts')
def update_contract(user_data, user_permissions):
    """
    Mettre à jour un contrat existant.
    """
    contract_id = click.prompt('ID du contrat à mettre à jour', type=int)
    contract_controller = ContractController()

    # Récupérer le contrat par ID pour connaître l'ancien statut
    contract = contract_controller.get_contract_by_id(contract_id)
    if not contract:
        click.echo("Contrat introuvable.")
        contract_controller.close()
        return

    old_status = contract.status

    # Vérifier les permissions de l'utilisateur
    user_id = user_data.get('user_id')
    if 'can_modify_all_contracts' in user_permissions:
        # L'utilisateur peut modifier n'importe quel contrat
        pass  # Pas de vérification supplémentaire nécessaire
    elif 'can_modify_own_contracts' in user_permissions:
        # Vérifier que l'utilisateur est le commercial responsable
        if contract.sales_contact_id != user_id:
            click.echo("Vous n'êtes pas autorisé à modifier ce contrat.")
            contract_controller.close()
            return
    else:
        click.echo("Vous n'avez pas la permission de modifier des contrats.")
        contract_controller.close()
        return

    # Collecte des informations du contrat à mettre à jour avec valeurs par défaut
    amount = click.prompt('Nouveau montant total', default=contract.amount, type=float)
    remaining_amount = click.prompt('Nouveau montant restant', default=contract.remaining_amount, type=float)
    status = click.prompt('Nouveau statut (1 pour signé, 0 pour en attente)', default=int(contract.status), type=int)

    contract_data = {
        'amount': amount,
        'remaining_amount': remaining_amount,
        'status': bool(status),
    }
    try:
        # Mettre à jour le contrat via le contrôleur
        updated_contract = contract_controller.update_contract(contract_id, contract_data)
        # contract_controller.close()

        if updated_contract:
            # Journalisation de la mise à jour du contrat
            if old_status is False and updated_contract.status is True:
                # Journalisation spécifique pour un contrat signé
                log_info(
                    logger,
                    f"Contrat signé avec succès : ID {updated_contract.id} commercial: {updated_contract.sales_contact.fullname}"
                )
                click.echo(f"Contrat signé avec succès : ID {updated_contract.id}")
            else:
                log_info(
                    logger,
                    f"Contrat mis à jour avec succès : ID {updated_contract.id} commercial: {updated_contract.sales_contact.fullname}"
                )
                click.echo(f"Contrat mis à jour avec succès : ID {updated_contract.id}")
            console = Console()
            table = Table(title="Contrat mis à jour avec succès", show_header=False)
            table.add_column("champ", style="bold cyan")
            table.add_column("valeur", style="bold magenta")
            table.add_row("ID", str(updated_contract.id))
            table.add_row("Client", updated_contract.client.fullname)
            table.add_row("Montant total", str(updated_contract.amount))
            table.add_row("Montant restant", str(updated_contract.remaining_amount))
            table.add_row("Commercial", updated_contract.sales_contact.fullname)
            console.print(table)
        else:
            click.echo("Erreur lors de la mise à jour du contrat.")
    except ValueError as ve:
        # Erreur métier pas d'envvoi vers Sentry
        click.echo(f"Erreur lors de la mise à jour du contrat:{ve}")
        contract_controller.close()
    except Exception as e:
        # Erreur inattendue, on log_error et affiche un message générique
        log_error(logger, f"Erreur inattendue lors de la mise à jour du contrat : {str(e)}")
        click.echo("Erreur lors de la mise à jour du contrat.")
        contract_controller.close()


# Commande pour lister tous les contrats
@contracts.command(name='list-contracts', aliases=[''])
@require_permission('can_filter_contracts')
@click.option('--status', type=click.Choice(['signed', 'unsigned']), help='Filtrer par statut du contrat ("signed" ou "unsigned")')
@click.option('--payment', type=click.Choice(['paid', 'unpaid']), help='Filtrer par paiement ("paid" ou "unpaid")')
@click.option('--own', is_flag=True, help='Afficher uniquement les contrats dont vous êtes le commercial.')
def list_contracts(user_data, status, payment, own):
    """
    list-contracts: Afficher tous les contrats.
    """
    contract_controller = ContractController()
    contracts = contract_controller.get_all_contracts()
    contract_controller.close()

    # Filtrer les contrats dont l'utilisateur est le commercial si l'option --own est utilisée
    if own:
        contracts = [c for c in contracts if c.sales_contact_id == user_data['user_id']]

    # Appliquer les filtres
    if status == 'signed':
        contracts = [c for c in contracts if c.status]
    elif status == 'unsigned':
        contracts = [c for c in contracts if not c.status]

    if payment == 'paid':
        contracts = [c for c in contracts if c.remaining_amount == 0]
    elif payment == 'unpaid':
        contracts = [c for c in contracts if c.remaining_amount > 0]

    if not contracts:
        # Construire le message d'erreur personnalisé
        criteria = []
        if own:
            criteria.append("dont vous êtes le commercial")
        if status:
            criteria.append(f"statut '{status}'")
        if payment:
            criteria.append(f"paiement '{payment}'")
        if criteria:
            criteria_str = " et ".join(criteria)
            click.echo(f"Aucun contrat trouvé avec les critères : {criteria_str}.")
        else:
            click.echo("Aucun contrat trouvé.")
        return

    console = Console()
    table = Table(
        title="Liste des contrats",
        show_header=True, header_style="bold magenta",
        show_lines=True)
    table.add_column("ID", style="dim")
    table.add_column("Nom du client")
    table.add_column("Commercial")
    table.add_column("Montant total")
    table.add_column("Montant restant")
    table.add_column("Date de création")
    table.add_column("Statut")

    for contract in contracts:
        table.add_row(
            str(contract.id),
            contract.client.fullname if contract.client else "N/A",
            contract.sales_contact.fullname if contract.sales_contact else "N/A",
            str(contract.amount),
            str(contract.remaining_amount),
            contract.date_created.strftime("%d/%m/%Y %H:%M"),
            "Signé" if contract.status else "En attente"
        )
    console.print(table)


@contracts.command(name='delete')
@require_permission('can_delete_contracts')
def delete_contract(user_data):
    """
    Supprimer un contrat existant.
    """
    contract_id = click.prompt('ID du contrat à supprimer', type=int)
    contract_controller = ContractController()

    contract = contract_controller.get_contract_by_id(contract_id)
    if not contract:
        click.echo("Contrat introuvable.")
        contract_controller.close()
        return

    try:
        success = contract_controller.delete_contract(contract_id)
        contract_controller.close()
        if success:
            # Journaliser le succès
            log_info(logger, f"Contrat ID {contract_id} supprimé avec succès.")
            click.echo(f"Contrat ID {contract_id} supprimé avec succès.")
        else:
            click.echo("Impossible de supprimer le contrat (inexistant ?).")

    except ValueError as ve:
        # Erreur métier, pas besoin de log_error
        click.echo(f"Erreur lors de la suppression du contrat : {ve}")
        contract_controller.close()
    except Exception as e:
        log_error(logger, f"Erreur inattendue lors de la suppression du contrat : {str(e)}")
        click.echo("Erreur lors de la suppression du contrat.")
        contract_controller.close()
