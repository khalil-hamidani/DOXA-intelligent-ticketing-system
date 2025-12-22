# kb/kb_manager.py
"""
Gestionnaire de Knowledge Base avec RAG (Retrieval-Augmented Generation)
Utilise ChromaDB pour le stockage vectoriel
"""

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import json
from loguru import logger
from config.settings import settings

class KnowledgeBaseManager:
    """Gère l'indexation et la recherche dans la KB"""
    
    def __init__(self):
        self.persist_dir = Path(settings.chroma_persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialiser ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.persist_dir)
        )
        
        # Collection principale
        self.collection = self.chroma_client.get_or_create_collection(
            name="support_kb",
            metadata={"description": "Support Knowledge Base"}
        )
        
        # Modèle d'embedding
        self.embedding_model = SentenceTransformer(settings.embedding_model)
        
        logger.info(f"KB initialized with {self.collection.count()} documents")
    
    def add_document(
        self, 
        doc_id: str, 
        text: str, 
        metadata: Optional[Dict] = None
    ) -> bool:
        """Ajoute un document à la KB"""
        try:
            # Générer embedding
            embedding = self.embedding_model.encode(text).tolist()
            
            # Ajouter à ChromaDB
            self.collection.add(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[text],
                metadatas=[metadata or {}]
            )
            
            logger.info(f"Document {doc_id} added to KB")
            return True
            
        except Exception as e:
            logger.error(f"Error adding document {doc_id}: {e}")
            return False
    
    def search(
        self, 
        query: str, 
        n_results: int = 5,
        category_filter: Optional[str] = None
    ) -> List[Dict]:
        """Recherche sémantique dans la KB"""
        try:
            # Générer embedding de la requête
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Filtre optionnel par catégorie
            where_filter = None
            if category_filter:
                where_filter = {"category": category_filter}
            
            # Recherche
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_filter
            )
            
            # Formater résultats
            documents = []
            for i in range(len(results['ids'][0])):
                documents.append({
                    'id': results['ids'][0][i],
                    'text': results['documents'][0][i],
                    'distance': results['distances'][0][i],
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {}
                })
            
            logger.info(f"Found {len(documents)} relevant documents for query")
            return documents
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    def update_document(self, doc_id: str, text: str, metadata: Optional[Dict] = None) -> bool:
        """Met à jour un document existant"""
        try:
            embedding = self.embedding_model.encode(text).tolist()
            
            self.collection.update(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[text],
                metadatas=[metadata or {}]
            )
            
            logger.info(f"Document {doc_id} updated")
            return True
            
        except Exception as e:
            logger.error(f"Error updating document {doc_id}: {e}")
            return False
    
    def delete_document(self, doc_id: str) -> bool:
        """Supprime un document"""
        try:
            self.collection.delete(ids=[doc_id])
            logger.info(f"Document {doc_id} deleted")
            return True
        except Exception as e:
            logger.error(f"Error deleting document {doc_id}: {e}")
            return False
    
    def bulk_import_from_json(self, json_file: Path) -> int:
        """Importe plusieurs documents depuis un fichier JSON"""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                documents = json.load(f)
            
            count = 0
            for doc in documents:
                if self.add_document(
                    doc_id=doc.get('id'),
                    text=doc.get('text'),
                    metadata=doc.get('metadata', {})
                ):
                    count += 1
            
            logger.info(f"Imported {count} documents from {json_file}")
            return count
            
        except Exception as e:
            logger.error(f"Bulk import error: {e}")
            return 0
    
    def get_stats(self) -> Dict:
        """Statistiques de la KB"""
        return {
            'total_documents': self.collection.count(),
            'collection_name': self.collection.name
        }

# Instance globale
kb_manager = KnowledgeBaseManager()


# Exemple de données à importer dans kb/documents/sample_kb.json
SAMPLE_KB_DATA = [
    {
        "id": "fact_001",
        "text": "Pour modifier votre adresse de facturation, connectez-vous à votre espace client, section 'Mon compte' > 'Facturation' > 'Modifier l'adresse'. Les modifications prennent effet immédiatement.",
        "metadata": {
            "category": "facturation",
            "keywords": ["facturation", "adresse", "modification"],
            "confidence": 0.95
        }
    },
    {
        "id": "tech_001",
        "text": "Si vous rencontrez une erreur 500 lors de la connexion, vérifiez d'abord votre connexion internet. Ensuite, videz le cache de votre navigateur (Ctrl+Shift+Del). Si le problème persiste, contactez le support technique.",
        "metadata": {
            "category": "technique",
            "keywords": ["erreur", "500", "connexion", "cache"],
            "confidence": 0.92
        }
    },
    {
        "id": "tech_002",
        "text": "Pour réinitialiser votre mot de passe, cliquez sur 'Mot de passe oublié' sur la page de connexion. Un email de réinitialisation sera envoyé à votre adresse enregistrée. Le lien expire après 24 heures.",
        "metadata": {
            "category": "technique",
            "keywords": ["mot de passe", "réinitialisation", "oublié"],
            "confidence": 0.98
        }
    },
    {
        "id": "fact_002",
        "text": "Les factures sont générées automatiquement le 1er de chaque mois et envoyées par email. Vous pouvez télécharger toutes vos factures depuis la section 'Historique de facturation' de votre compte.",
        "metadata": {
            "category": "facturation",
            "keywords": ["facture", "téléchargement", "historique"],
            "confidence": 0.90
        }
    },
    {
        "id": "bug_001",
        "text": "Si vous constatez que des données ne se sauvegardent pas correctement, assurez-vous d'utiliser la dernière version de l'application. Mettez à jour via le menu 'Paramètres' > 'Mise à jour'. Redémarrez ensuite l'application.",
        "metadata": {
            "category": "bug",
            "keywords": ["sauvegarde", "données", "mise à jour"],
            "confidence": 0.88
        }
    },
    {
        "id": "feat_001",
        "text": "Notre système supporte l'export de données en formats CSV, Excel et PDF. Pour exporter vos données, accédez à la section concernée et cliquez sur le bouton 'Exporter'. Sélectionnez le format désiré.",
        "metadata": {
            "category": "feature_request",
            "keywords": ["export", "CSV", "Excel", "PDF"],
            "confidence": 0.93
        }
    }
]