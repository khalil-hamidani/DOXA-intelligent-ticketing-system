"""
Script pour tester le système complet
Lance des tickets de test et affiche les résultats
"""

import requests
import json
from time import sleep

BASE_URL = "http://localhost:8000"

# Tickets de test
TEST_TICKETS = [
    {
        "client_name": "Alice Martin",
        "email": "alice.martin@example.com",
        "subject": "Problème de connexion urgent",
        "description": "Je ne peux plus me connecter à mon compte depuis ce matin. J'ai essayé de réinitialiser mon mot de passe mais je ne reçois pas l'email. C'est urgent car j'ai une présentation importante cet après-midi."
    },
    {
        "client_name": "Bob Dupont",
        "email": "bob.dupont@example.com",
        "subject": "Question sur ma facture",
        "description": "Bonjour, j'ai reçu ma facture du mois dernier mais je ne comprends pas certains montants. Pouvez-vous m'expliquer à quoi correspondent les frais de 15€ ?"
    },
    {
        "client_name": "Charlie Dubois",
        "email": "charlie.dubois@example.com",
        "subject": "Bug dans l'application",
        "description": "Chaque fois que j'essaie de sauvegarder mes données, l'application plante. J'ai essayé de redémarrer mais le problème persiste. J'utilise la version 2.3.1 sur Windows 10."
    },
    {
        "client_name": "Diana Laurent",
        "email": "diana.laurent@example.com",
        "subject": "Demande de nouvelle fonctionnalité",
        "description": "Serait-il possible d'ajouter une fonction d'export en PDF ? Ce serait très utile pour partager les rapports avec mes collègues."
    }
]

def test_ticket_creation():
    """Test de création et traitement de tickets"""
    
    print("🧪 TESTING AI TICKETING SYSTEM\n")
    print("=" * 60)
    
    for i, ticket_data in enumerate(TEST_TICKETS, 1):
        print(f"\n📝 Test {i}/{len(TEST_TICKETS)}: {ticket_data['subject']}")
        print("-" * 60)
        
        # Créer le ticket
        response = requests.post(f"{BASE_URL}/tickets", json=ticket_data)
        
        if response.status_code == 200:
            result = response.json()
            ticket_id = result['ticket_id']
            process_result = result['result']
            
            print(f"✅ Ticket créé: {ticket_id}")
            print(f"📊 Statut: {process_result.get('status')}")
            print(f"🎯 Confiance: {process_result.get('confidence', 'N/A')}")
            print(f"🔄 Tentatives: {process_result.get('attempts', 'N/A')}")
            print(f"🚨 Escaladé: {process_result.get('escalated', False)}")
            
            if not process_result.get('escalated'):
                print(f"\n💬 Réponse générée:")
                print(process_result.get('response', '').strip()[:200] + "...")
            else:
                print(f"\n⚠️ Raison escalade: {process_result.get('reason')}")
            
        else:
            print(f"❌ Erreur: {response.status_code}")
            print(response.text)
        
        sleep(1)  # Pause entre les tests
    
    print("\n" + "=" * 60)
    print("✨ Tests terminés!")

def test_kb_stats():
    """Affiche les stats de la KB"""
    print("\n📚 Knowledge Base Statistics")
    print("-" * 60)
    
    response = requests.get(f"{BASE_URL}/kb/stats")
    if response.status_code == 200:
        stats = response.json()
        print(json.dumps(stats, indent=2))

def test_feedback():
    """Test du système de feedback"""
    print("\n📬 Testing Feedback System")
    print("-" * 60)
    
    # Créer un ticket simple
    ticket_data = {
        "client_name": "Test User",
        "email": "test@example.com",
        "subject": "Test feedback",
        "description": "Ceci est un test du système de feedback pour vérifier le fonctionnement de la boucle de retry."
    }
    
    response = requests.post(f"{BASE_URL}/tickets", json=ticket_data)
    ticket_id = response.json()['ticket_id']
    
    print(f"✅ Ticket test créé: {ticket_id}")
    
    # Feedback négatif
    feedback = {
        "satisfied": False,
        "reason": "La solution proposée ne fonctionne pas. Pouvez-vous être plus précis ?"
    }
    
    print("\n📤 Envoi feedback négatif...")
    response = requests.post(f"{BASE_URL}/tickets/{ticket_id}/feedback", json=feedback)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Feedback traité")
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    import sys
    
    print("🎫 AI TICKETING SYSTEM - TEST SUITE")
    print("=" * 60)
    
    # Vérifier que l'API est en ligne
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code != 200:
            print("❌ API not responding. Start it with: python main.py")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Start it with: python main.py")
        sys.exit(1)
    
    # Lancer les tests
    test_kb_stats()
    test_ticket_creation()
    test_feedback()
    
    print("\n✨ All tests completed!")
    print("\n💡 Tips:")
    print("  - View all tickets: curl http://localhost:8000/tickets")
    print("  - View specific ticket: curl http://localhost:8000/tickets/{ticket_id}")
    print("  - KB stats: curl http://localhost:8000/kb/stats")