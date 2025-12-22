"""
Script d'initialisation de la Knowledge Base
Charge les documents de base pour démarrer le système
"""

import json
from pathlib import Path
from kb.kb_manager import kb_manager
from loguru import logger

# Données d'exemple pour la KB
SAMPLE_DOCUMENTS = [
    {
        "id": "fact_001",
        "text": "Pour modifier votre adresse de facturation, connectez-vous à votre espace client, section 'Mon compte' > 'Facturation' > 'Modifier l'adresse'. Les modifications prennent effet immédiatement pour les prochaines factures.",
        "metadata": {
            "category": "facturation",
            "keywords": ["facturation", "adresse", "modification", "compte"],
            "confidence": 0.95,
            "last_updated": "2025-01-15"
        }
    },
    {
        "id": "fact_002",
        "text": "Les factures sont générées automatiquement le 1er de chaque mois et envoyées par email à l'adresse enregistrée. Vous pouvez télécharger toutes vos factures depuis la section 'Historique de facturation' de votre espace client. Les factures sont disponibles en format PDF.",
        "metadata": {
            "category": "facturation",
            "keywords": ["facture", "téléchargement", "historique", "PDF"],
            "confidence": 0.90
        }
    },
    {
        "id": "fact_003",
        "text": "Les moyens de paiement acceptés sont : carte bancaire (Visa, Mastercard), virement bancaire et prélèvement automatique. Pour modifier votre moyen de paiement, accédez à 'Mon compte' > 'Paiement' > 'Gérer mes moyens de paiement'.",
        "metadata": {
            "category": "facturation",
            "keywords": ["paiement", "carte", "virement", "prélèvement"],
            "confidence": 0.92
        }
    },
    {
        "id": "tech_001",
        "text": "Si vous rencontrez une erreur 500 lors de la connexion, suivez ces étapes : 1) Vérifiez votre connexion internet, 2) Videz le cache de votre navigateur (Ctrl+Shift+Del ou Cmd+Shift+Del), 3) Essayez avec un autre navigateur, 4) Si le problème persiste, contactez le support technique en précisant l'heure exacte de l'erreur.",
        "metadata": {
            "category": "technique",
            "keywords": ["erreur", "500", "connexion", "cache", "navigateur"],
            "confidence": 0.92
        }
    },
    {
        "id": "tech_002",
        "text": "Pour réinitialiser votre mot de passe : 1) Cliquez sur 'Mot de passe oublié' sur la page de connexion, 2) Entrez votre adresse email, 3) Vérifiez votre boîte mail (et spam), 4) Cliquez sur le lien de réinitialisation (valide 24h), 5) Créez un nouveau mot de passe (min. 8 caractères, 1 majuscule, 1 chiffre).",
        "metadata": {
            "category": "technique",
            "keywords": ["mot de passe", "réinitialisation", "oublié", "email"],
            "confidence": 0.98
        }
    },
    {
        "id": "tech_003",
        "text": "Si l'application ne démarre pas : 1) Vérifiez que vous avez la dernière version (Menu > À propos), 2) Redémarrez votre ordinateur, 3) Désinstallez et réinstallez l'application, 4) Vérifiez les droits d'administrateur sous Windows, 5) Sur Mac, autorisez l'application dans Préférences > Sécurité.",
        "metadata": {
            "category": "technique",
            "keywords": ["application", "démarrage", "installation", "version"],
            "confidence": 0.88
        }
    },
    {
        "id": "bug_001",
        "text": "Si vos données ne se sauvegardent pas correctement : 1) Assurez-vous d'avoir une connexion internet stable, 2) Vérifiez que vous utilisez la dernière version de l'application (Menu > Paramètres > Mise à jour), 3) Vérifiez l'espace disque disponible (min. 500 MB requis), 4) Redémarrez l'application après la mise à jour.",
        "metadata": {
            "category": "bug",
            "keywords": ["sauvegarde", "données", "mise à jour", "version"],
            "confidence": 0.88
        }
    },
    {
        "id": "bug_002",
        "text": "Si vous voyez des caractères bizarres à la place du texte : 1) Vérifiez l'encodage (UTF-8 recommandé), 2) Mettez à jour votre navigateur, 3) Videz le cache, 4) Si le problème persiste sur un document spécifique, ré-uploadez-le. Ce problème survient souvent avec des fichiers créés sur des versions anciennes.",
        "metadata": {
            "category": "bug",
            "keywords": ["encodage", "caractères", "affichage", "UTF-8"],
            "confidence": 0.85
        }
    },
    {
        "id": "feat_001",
        "text": "L'export de données est disponible en plusieurs formats : CSV (compatible Excel), Excel (.xlsx), PDF et JSON. Pour exporter : 1) Accédez à la section concernée, 2) Cliquez sur le bouton 'Exporter' (icône téléchargement), 3) Sélectionnez le format désiré, 4) Choisissez les filtres si nécessaire, 5) Téléchargez le fichier.",
        "metadata": {
            "category": "feature_request",
            "keywords": ["export", "CSV", "Excel", "PDF", "JSON"],
            "confidence": 0.93
        }
    },
    {
        "id": "feat_002",
        "text": "Pour partager des documents avec des collaborateurs : 1) Ouvrez le document, 2) Cliquez sur 'Partager' (icône personne+), 3) Entrez l'email du collaborateur, 4) Choisissez les permissions (lecture seule ou édition), 5) Ajoutez un message optionnel, 6) Envoyez. Le collaborateur recevra un email avec un lien d'accès.",
        "metadata": {
            "category": "feature_request",
            "keywords": ["partage", "collaborateur", "permissions", "accès"],
            "confidence": 0.90
        }
    },
    {
        "id": "account_001",
        "text": "Pour créer un compte : 1) Cliquez sur 'S'inscrire', 2) Entrez vos informations (nom, email, mot de passe), 3) Acceptez les conditions d'utilisation, 4) Validez votre email (cliquez sur le lien reçu), 5) Complétez votre profil. L'inscription est gratuite pour le plan de base.",
        "metadata": {
            "category": "autre",
            "keywords": ["inscription", "compte", "création", "email"],
            "confidence": 0.94
        }
    },
    {
        "id": "account_002",
        "text": "Pour supprimer votre compte : 1) Accédez à 'Mon compte' > 'Paramètres', 2) Faites défiler jusqu'à 'Zone de danger', 3) Cliquez sur 'Supprimer mon compte', 4) Confirmez en entrant votre mot de passe, 5) Vos données seront supprimées sous 30 jours (délai légal). Attention : cette action est irréversible après 30 jours.",
        "metadata": {
            "category": "autre",
            "keywords": ["suppression", "compte", "données", "RGPD"],
            "confidence": 0.96
        }
    },
    {
        "id": "perf_001",
        "text": "Si l'application est lente : 1) Fermez les onglets/applications inutiles, 2) Vérifiez votre connexion internet (speedtest), 3) Videz le cache de l'application, 4) Sur mobile, fermez les apps en arrière-plan, 5) Redémarrez l'appareil. Les performances optimales requièrent : 4GB RAM min, connexion 5 Mbps min.",
        "metadata": {
            "category": "technique",
            "keywords": ["lenteur", "performance", "optimisation", "RAM"],
            "confidence": 0.87
        }
    },
    {
        "id": "security_001",
        "text": "Pour sécuriser votre compte : 1) Utilisez un mot de passe fort (12+ caractères), 2) Activez l'authentification à deux facteurs (2FA) dans 'Mon compte' > 'Sécurité', 3) Ne partagez jamais votre mot de passe, 4) Déconnectez-vous sur les appareils partagés, 5) Vérifiez régulièrement les connexions actives dans 'Sécurité' > 'Appareils connectés'.",
        "metadata": {
            "category": "autre",
            "keywords": ["sécurité", "mot de passe", "2FA", "authentification"],
            "confidence": 0.95
        }
    },
    {
        "id": "mobile_001",
        "text": "L'application mobile est disponible sur iOS (11+) et Android (8+). Fonctionnalités : synchronisation automatique avec le web, notifications push, mode hors-ligne, scan de documents. Pour télécharger : App Store ou Google Play. Recherchez 'Votre App'. La première synchronisation peut prendre quelques minutes selon le volume de données.",
        "metadata": {
            "category": "autre",
            "keywords": ["mobile", "iOS", "Android", "synchronisation"],
            "confidence": 0.91
        }
    }
]

def initialize_kb():
    """Initialise la Knowledge Base avec les documents de base"""
    
    logger.info("🚀 Initializing Knowledge Base...")
    
    # Créer le dossier documents si nécessaire
    docs_dir = Path("kb/documents")
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    # Sauvegarder les documents en JSON
    json_file = docs_dir / "initial_kb.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(SAMPLE_DOCUMENTS, f, indent=2, ensure_ascii=False)
    
    logger.info(f"📁 Saved {len(SAMPLE_DOCUMENTS)} documents to {json_file}")
    
    # Charger dans ChromaDB
    success_count = 0
    for doc in SAMPLE_DOCUMENTS:
        if kb_manager.add_document(
            doc_id=doc['id'],
            text=doc['text'],
            metadata=doc['metadata']
        ):
            success_count += 1
    
    logger.info(f"✅ Successfully loaded {success_count}/{len(SAMPLE_DOCUMENTS)} documents into KB")
    
    # Afficher les stats
    stats = kb_manager.get_stats()
    logger.info(f"📊 KB Stats: {stats}")
    
    return success_count

if __name__ == "__main__":
    print("=" * 60)
    print("🎫 AI TICKETING SYSTEM - KB INITIALIZATION")
    print("=" * 60)
    print()
    
    count = initialize_kb()
    
    print()
    print("=" * 60)
    print(f"✨ Initialization complete! {count} documents loaded.")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Start the API: python main.py")
    print("2. Run tests: python test_system.py")
    print("3. Access API docs: http://localhost:8000/docs")
    print()

