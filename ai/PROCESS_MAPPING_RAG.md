# Mapping: Processus Métier ↔ Architecture RAG + Agents

**Date**: December 22, 2025  
**Purpose**: Aligner le processus complet de traitement des tickets avec l'architecture RAG Pipeline + agents existants  
**Status**: ✅ Mapping complet

---

## 📋 Vue d'ensemble du processus métier

```
Client soumet ticket
         ↓
    [ÉTAPE 0: VALIDATION] ← agents/validator.py
         ↓
    [ÉTAPE 1: SCORING] ← agents/scorer.py
         ↓
    [ÉTAPE 2: QUERY ANALYSIS] ← agents/query_analyzer.py + agents/classifier.py
         ↓
    [ÉTAPE 3: SOLUTION FINDING] ← pipeline/RAG (retrieval + ranking)
         ↓
    [ÉTAPE 4: EVALUATION] ← agents/evaluator.py
         ↓
        / \
    Confiance? 
    / (>60%)  \
  OUI          NON
  ↓             ↓
[COMPOSER]  [ESCALADE]
  ↓             ↓
[ENVOYER]   [HUMAIN]
  ↓             ↓
[FEEDBACK]  [POST-ANALYSE]
  ↓             ↓
  └─→ [AMÉLIORATION CONTINUE] ← agents/continuous_improvement.py
         ↓
    [FERMETURE]
```

---

## 🔍 Mapping détaillé par étape

### **ÉTAPE 0: Validation Initiale**

**Responsabilité**: Vérifier que le ticket contient suffisamment d'information

| Aspect | Module | Responsable |
|--------|--------|-------------|
| **Vérification** | `agents/validator.py` | Agent Validator |
| **Input** | Ticket brut (formulaire client) | Client |
| **Checks** | Context, keywords, éléments exploitables | `QueryValidator` (pipeline) |
| **Output** | Ticket valide ✅ ou Rejeté ❌ | |
| **Action rejet** | Demander au client de compléter | Client notification |

**Code existant**:
```python
# agents/validator.py
# vérifie: context_clarity, keyword_extractability, exploitability

# pipeline/query_intelligence.py → QueryValidator
# valide: length, keywords, spam detection, low-signal queries
```

---

### **ÉTAPE 1: Scoring & Priorisation**

**Responsabilité**: Calculer un score de priorité basé sur urgence, récurrence, SLA

| Aspect | Module | Responsable |
|--------|--------|-------------|
| **Scoring** | `agents/scorer.py` | Agent Scorer |
| **Critères** | Urgence, récurrence, impact business, SLA | Config |
| **Output** | Score (0-100) → Priorité file | |
| **Utilisation** | Ordonnance de traitement | Queue manager |

**Code existant**:
```python
# agents/scorer.py
# calcule: urgency_score, recurrence_score, business_impact_score
# génère: ticket_priority
```

---

### **ÉTAPE 2: Query Analysis**

**Responsabilité**: Comprendre le problème du client (2 agents)

#### **Agent A: Analyse & Reformulation**

| Aspect | Module | Responsable |
|--------|--------|-------------|
| **Résumé** | `agents/query_analyzer.py` | Agent Query Analyzer |
| **Reformulation** | Pipeline input processing | |
| **Extraction keywords** | `pipeline/query_intelligence.py` → `QueryAugmenter` | |
| **Output** | Ticket reformulé + keywords | |

**Code existant**:
```python
# agents/query_analyzer.py
# résume et reformule le ticket
# extrait les entités et keywords

# pipeline/query_intelligence.py → QueryAugmenter
# rephrasing, expansion, synonym extraction
```

#### **Agent B: Classification**

| Aspect | Module | Responsable |
|--------|--------|-------------|
| **Classification** | `agents/classifier.py` | Agent Classifier |
| **Catégories** | technique, facturation, authentification, autre | |
| **Scores** | `pipeline/query_intelligence.py` → `MulticlassClassifier` | Per-class scores |
| **Type traitement** | Détermine route (support, billing, escalade...) | |
| **Output** | Catégorie + type de traitement | |

**Code existant**:
```python
# agents/classifier.py
# classifie le ticket en catégories

# pipeline/query_intelligence.py → MulticlassClassifier
# per-class semantic scores (0-1)
# FIX: élimine le problème de "double classification"
```

---

### **ÉTAPE 3: Solution Finding (RAG Core)**

**Responsabilité**: Trouver les documents KB pertinents et construire le contexte

| Aspect | Module | Responsable |
|--------|--------|-------------|
| **Query Encoding** | `pipeline/retrieval.py` → `VectorRetriever` | Embeddings |
| **Vector Search** | `rag/vector_store.py` | Cosine similarity |
| **Document Retrieval** | `pipeline/retrieval.py` → `ContextualRetriever` | Top-k + fallback |
| **Ranking** | `pipeline/ranking.py` → `RankingPipeline` | 4 rankers |
| **Context Building** | `pipeline/context.py` → `ContextBuilder` | Token-aware |
| **Output** | Context structuré pour LLM | |

**Code existant - RAG Pipeline**:
```python
# pipeline/retrieval.py
# - embed query
# - search vector store
# - return results with similarity scores

# pipeline/ranking.py
# - semantic ranker (embedding similarity)
# - keyword ranker (BM25-like)
# - hybrid ranker (combinaison)
# - metadata ranker (category/priority/recency)

# pipeline/context.py
# - DocumentMerger (3 strategies)
# - ContextChunker (token-aware)
# - ContextOptimizer (greedy selection)
# - ContextBuilder (LLM-ready format)
```

**KB Data** (responsabilité data prep team):
```python
chunks = [
    {
        "id": "chunk_001",
        "content": "Solution/documentation text...",
        "metadata": {
            "category": "technique|facturation|authentification|autre",
            "section": "Installation|Troubleshooting|etc",
            "source": "help_docs|faq|manual",
            "priority": "high|medium|low"
        }
    }
]
```

---

### **ÉTAPE 4: Evaluation & Confidence**

**Responsabilité**: Évaluer la confiance de la solution trouvée

| Aspect | Module | Responsable |
|--------|--------|-------------|
| **Confiance** | `agents/evaluator.py` | Agent Evaluator |
| **Calcul** | Score de confiance (0-100%) | |
| **Détection** | Cas non-standards, émotions, données sensibles | `ResponseValidator` (pipeline) |
| **Décision** | Confiance > 60% ? | |
| **Output** | Score + recommandation (répondre ou escalader) | |

**Code existant**:
```python
# agents/evaluator.py
# calcule confidence_score
# détecte anomalies, emotions, données sensibles

# pipeline/answer.py → ResponseValidator
# vérifie answer_length, confidence_threshold
# détecte escalation_indicators
```

---

### **ÉTAPE 5: Response Composition (Confiance > 60%)**

**Responsabilité**: Générer une réponse structurée au client

| Aspect | Module | Responsable |
|--------|--------|-------------|
| **Input** | Ticket + contexte RAG | |
| **LLM Call** | `pipeline/answer.py` → `ContextAwareAnswerGenerator` | Mistral |
| **Structure** | Remerciements, reformulation, solution, étapes | |
| **Output** | Réponse finale complète | |

**Code existant**:
```python
# pipeline/answer.py
# - AnswerGenerator (LLM call via Agno)
# - ContextAwareAnswerGenerator (integrates context)
# - ResponseValidator (quality checks)

# agents/response_composer.py
# - formatte la réponse finale
# - ajoute remerciements, structure
```

---

### **ÉTAPE 6: Envoi & Feedback Client**

**Responsabilité**: Envoyer la réponse et récolter le feedback

| Aspect | Module | Responsable |
|--------|--------|-------------|
| **Envoi** | Email send (notification) | |
| **Feedback** | Client satisfaction (oui/non) | Client |
| **Cas 1: ✅ Satisfait** | Clôture ticket + archivage | |
| **Cas 2: ❌ Non satisfait** | Relance Query Analyzer (max 2 tentatives) | Loop back to step 2 |

**Code existant**:
```python
# agents/feedback_handler.py
# - récolte satisfaction client
# - décide: clôture ou relance
# - compte max_attempts
```

---

### **ÉTAPE 7: Escalade Humaine (Confiance < 60%)**

**Responsabilité**: Router vers agent humain si nécessaire

| Aspect | Module | Responsable |
|--------|--------|-------------|
| **Trigger** | Confiance < 60% OU max_attempts=2 atteint | |
| **Escalade** | `agents/escalation_manager.py` | Agent Escalation |
| **Assignation** | Routing vers support humain | Support team |
| **Email** | Notification automatique au client | |
| **Status** | "Escaladé - En attente humain" | |

**Code existant**:
```python
# agents/escalation_manager.py
# - détecte escalation triggers
# - assigne à humain
# - crée contexte escalade
# - envoie email client
```

---

### **ÉTAPE 8: Post-analyse Humaine**

**Responsabilité**: Qualifier l'escalade

| Aspect | Module | Responsable |
|--------|--------|-------------|
| **Qualification** | Escalade justifiée ou non | Support humain |
| **Catégories** | Hallucination IA, manque KB, données sensibles, etc. | |
| **Marquage** | Flag pour amélioration continue | DB |

**Code existant**:
```python
# agents/escalation_manager.py
# stocke escalade_reason, human_analysis
```

---

### **ÉTAPE 9: Amélioration Continue**

**Responsabilité**: Analyser tous les escaladés, identifier patterns, enrichir KB

| Aspect | Module | Responsable |
|--------|--------|-------------|
| **Analyse** | `agents/continuous_improvment.py` | Agent CI |
| **Patterns** | Détecte problèmes récurrents | |
| **KB Update** | Propose mise à jour KB | Data team |
| **Hallucination** | Détecte & marque errors LLM | |
| **Feedback Cycle** | Alimente amélioration modèles | |

**Code existant**:
```python
# agents/continuous_improvment.py
# - analyse escalades
# - détecte patterns
# - génère KB_updates
# - marque hallucinations
```

---

### **ÉTAPE 10: Métriques & Reporting**

**Responsabilité**: Collecter et analyser les performances

| Aspect | Module | Responsable |
|--------|--------|-------------|
| **Satisfaction** | % tickets clients satisfaits | |
| **Escalade Rate** | % escaladés | |
| **Confiance** | Score moyen de confiance | |
| **Cycle time** | Temps résolution moyen | |
| **Quality** | Évolution performance modèle | |

**Code existant**:
```python
# pipeline/orchestrator.py
# - RAGPipeline.get_stats()
# - récolte metrics par stage

# agents/feedback_handler.py
# - calcule satisfaction_rate
# - calcule escalation_rate
```

---

## 🎯 Points d'intégration RAG Pipeline

### **1. Où RAG intervient dans le flux**

```
Étape 0: Validation
    ↓
Étape 1: Scoring + Classification
    ↓
[ENTRÉE RAG] ← Query reformulé + classified
    ↓
Étape 3: Solution Finding (RAG Core)
    ├─ Query Intelligence (reformulation, augmentation)
    ├─ Retrieval (semantic search on KB)
    ├─ Ranking (4 strategies)
    └─ Context Building (token-aware)
    ↓
Étape 4: Evaluation (confiance sur réponse RAG)
    ↓
[SORTIE RAG] → Réponse complète + score de confiance
```

### **2. Input du RAG Pipeline**

```python
ticket = {
    "id": "t123",
    "category": "technique",  # From classifier
    "content": "Reformulated by query_analyzer",
    "keywords": ["keyword1", "keyword2"],  # From QueryAnalyzer
    "priority": 8,  # From scorer
    "client": {...}
}
```

### **3. Output du RAG Pipeline**

```python
result = {
    "stages": {
        "query_intelligence": {
            "validation": {...},
            "augmentation": {...},
            "classification": {...},
            "plan": {...}
        },
        "retrieval": {
            "query_embedding": [...],
            "results": [...],
            "similarity_scores": [0.87, 0.65, ...]
        },
        "ranking": {
            "method": "hybrid",
            "ranked_docs": [...],
            "scores": [...]
        },
        "context": {
            "merged_content": "...",
            "token_count": 1850,
            "document_count": 3
        },
        "answer": {
            "response": "Full answer to client",
            "confidence": 0.78
        },
        "validation": {
            "is_valid": True,
            "confidence_score": 0.78
        }
    },
    "final_response": "Full answer ready to send"
}
```

### **4. Confiance & Escalade Decision**

```python
confidence = result["stages"]["answer"]["confidence"]

if confidence < 0.60:
    # ESCALADE
    escalation_manager.escalate(ticket, confidence, reason)
else:
    # RÉPONDRE
    response_composer.compose(ticket, result["final_response"])
```

---

## 🔄 Loop de feedback (Max 2 tentatives)

```python
attempt = 1
max_attempts = 2

while attempt <= max_attempts:
    # Étape 0-1: Validation + Scoring (unchanged)
    
    # Étape 2: Query Analysis (reformulation différente possible)
    if attempt > 1:
        query_analyzer.reformulate_with_feedback(feedback)
    
    # Étape 3: RAG Pipeline
    rag_result = rag.process_ticket(ticket)
    
    # Étape 4: Evaluation
    confidence = rag_result["confidence"]
    
    if confidence > 0.60:
        # Répondre
        break
    elif attempt < max_attempts:
        # Relancer
        feedback = client_response["feedback"]
        attempt += 1
    else:
        # Escalader
        escalation_manager.escalate(ticket)
        break
```

---

## 📊 Data Flow Complet

```
CLIENT FORM
    ↓
[VALIDATOR] → Valid? ✅
    ↓
[SCORER] → Priority score
    ↓
[QUERY_ANALYZER] → Reformulated query
    ↓
[CLASSIFIER] → Category + type
    ↓
┌─────────────────────────────────────────┐
│     RAG PIPELINE (CORE)                 │
├─────────────────────────────────────────┤
│ 1. Query Intelligence                   │
│    - Validate (QueryValidator)          │
│    - Augment (QueryAugmenter)           │
│    - Classify (MulticlassClassifier)    │
│    - Plan (QueryPlanner)                │
│                                         │
│ 2. Retrieval                            │
│    - Embed query                        │
│    - Search vector store                │
│    - Filter by similarity               │
│    - Multi-step fallback                │
│                                         │
│ 3. Ranking                              │
│    - Semantic rank                      │
│    - Keyword rank                       │
│    - Hybrid rank                        │
│    - Metadata rank                      │
│                                         │
│ 4. Context                              │
│    - Merge documents                    │
│    - Chunk content                      │
│    - Optimize for LLM window            │
│    - Build prompt                       │
│                                         │
│ 5. Answer Generation                    │
│    - LLM call (Mistral)                 │
│    - Context integration                │
│    - Validate response                  │
│    - Score confidence                   │
└─────────────────────────────────────────┘
    ↓
[EVALUATOR] → Confidence score
    ↓
        ╱ confidence > 60% ?
       ╱           \
      ✅             ❌
      ↓              ↓
  [COMPOSER]    [ESCALATION_MGR]
      ↓              ↓
  [SEND_EMAIL]  [HUMAN_AGENT]
      ↓              ↓
  [FEEDBACK_HANDLER] 
      ↓
  Client satisfait? 
      ↓
   ✅ OUI: Clôture
   ❌ NON: Relance (max 2x)
      ↓
[CONTINUOUS_IMPROVEMENT]
      ↓
[METRICS & REPORTING]
```

---

## 💡 Architecture Finale: Agents + RAG

```
┌────────────────────────────────────────────────────┐
│         TICKET MANAGEMENT SYSTEM                   │
├────────────────────────────────────────────────────┤
│                                                    │
│  [VALIDATOR] → [SCORER] → [QUERY_ANALYZER]       │
│                               ↓                    │
│                        [CLASSIFIER]               │
│                               ↓                    │
│  ┌──────────────────────────────────────────┐    │
│  │  RAG PIPELINE (CORE INTELLIGENCE)        │    │
│  │  ─────────────────────────────────────  │    │
│  │  Query Intel → Retrieval → Ranking →    │    │
│  │  Context → Answer Generation             │    │
│  └──────────────────────────────────────────┘    │
│                      ↓                            │
│              [EVALUATOR] (confidence)            │
│                      ↓                            │
│              Confidence > 60%?                    │
│              /                \                   │
│           ✅ YES             ❌ NO                 │
│           ↓                   ↓                   │
│      [COMPOSER]      [ESCALATION_MGR]           │
│           ↓                   ↓                   │
│      [SEND_EMAIL]      [HUMAN_HANDLING]         │
│           ↓                   ↓                   │
│      [FEEDBACK_HANDLER] ← feedback ←            │
│           ↓                                      │
│     [CONTINUOUS_IMPROVEMENT]                    │
│           ↓                                      │
│    [METRICS & REPORTING]                        │
│                                                  │
└────────────────────────────────────────────────────┘
```

---

## ✅ Checklist: Modules requis

### **Agents existants** ✅
- [x] `agents/validator.py` - Validation initiale
- [x] `agents/scorer.py` - Scoring & priorisation
- [x] `agents/query_analyzer.py` - Reformulation
- [x] `agents/classifier.py` - Classification
- [x] `agents/evaluator.py` - Évaluation confiance
- [x] `agents/response_composer.py` - Composition réponse
- [x] `agents/escalation_manager.py` - Escalade humaine
- [x] `agents/feedback_handler.py` - Feedback & boucle
- [x] `agents/continuous_improvment.py` - Amélioration KB
- [x] `agents/orchestrator.py` - Orchestration agents

### **RAG Pipeline** ✅
- [x] `pipeline/query_intelligence.py` - Query processing
- [x] `pipeline/retrieval.py` - Semantic search
- [x] `pipeline/ranking.py` - Document ranking
- [x] `pipeline/context.py` - Context optimization
- [x] `pipeline/answer.py` - LLM-based generation
- [x] `pipeline/orchestrator.py` - Full pipeline orchestration
- [x] `rag/embeddings.py` - Embedding models
- [x] `rag/vector_store.py` - Vector storage
- [x] `config/pipeline_config.py` - Configuration

### **Integration points** ✅
- [x] Query analyzer output → RAG input
- [x] RAG output → Evaluator input
- [x] Evaluator output → Composer/Escalation decision
- [x] Feedback → Query analyzer (loop)

---

## 🎯 Summary: Mapping Process → Code

| Étape | Description | Primary Module | Secondary Modules |
|-------|-------------|-----------------|-------------------|
| **0** | Validation initiale | `validator.py` | `QueryValidator` (pipeline) |
| **1** | Scoring + Classification | `scorer.py` + `classifier.py` | `MulticlassClassifier` (pipeline) |
| **2** | Query Analysis | `query_analyzer.py` | `QueryAugmenter`, `QueryPlanner` (pipeline) |
| **3** | Solution Finding (RAG) | **RAG Pipeline** | `retrieval.py`, `ranking.py`, `context.py` |
| **4** | Évaluation | `evaluator.py` | `ResponseValidator` (pipeline) |
| **5** | Composition | `response_composer.py` | `ContextAwareAnswerGenerator` (pipeline) |
| **6** | Envoi + Feedback | `feedback_handler.py` | |
| **7** | Escalade humaine | `escalation_manager.py` | |
| **8** | Post-analyse | `escalation_manager.py` | |
| **9** | Amélioration continue | `continuous_improvment.py` | |
| **10** | Métriques | `orchestrator.py` | `RAGPipeline.get_stats()` |

---

## 🚀 Integration avec le RAG Pipeline

### **Cas d'usage 1: Utiliser RAG seul (Standalone)**
```python
from pipeline.orchestrator import SimplifiedRAGPipeline

rag = SimplifiedRAGPipeline()
rag.add_kb_documents(kb_chunks)

# Directement sans agents
answer = rag.answer_ticket(ticket)
```

### **Cas d'usage 2: Intégrer RAG dans agents existants (Hybrid)**
```python
# agents/orchestrator.py
ticket = Ticket(...)

# Étapes 0-2: Validation, Scoring, Analysis
validated = validator.validate(ticket)
scored = scorer.score(validated)
analyzed = query_analyzer.analyze(scored)
classified = classifier.classify(analyzed)

# Étape 3: RAG Pipeline
from pipeline.orchestrator import RAGPipeline
rag = RAGPipeline()
rag_result = rag.process_ticket(analyzed)

# Étapes 4+: Evaluation, Composition, Feedback
confidence = rag_result["stages"]["answer"]["confidence"]
if confidence > 0.60:
    composed = response_composer.compose(analyzed, rag_result)
    send_email(composed)
else:
    escalation_manager.escalate(analyzed, rag_result)
```

### **Cas d'usage 3: Remplacer agents par RAG (Progressive)**
```python
# Phase 1: Query Intelligence
# agents/query_analyzer + agents/classifier
# ↓ Remplacer par ↓
# pipeline/query_intelligence.py (validation, augmentation, classification)

# Phase 2: Solution Finding
# agents/solution_finder (KB search)
# ↓ Remplacer par ↓
# pipeline/retrieval + ranking + context (semantic RAG)

# Phase 3: Response
# agents/response_composer
# ↓ Utiliser ↓
# pipeline/answer.py (LLM-based generation)
```

---

## 📝 Notes importantes

### **1. Pas de duplication**
Le RAG Pipeline:
- ✅ Utilise déjà `query_intelligence.py` (analyse + classification)
- ✅ Enrichit solution_finder (RAG retrieval)
- ✅ Génère answers (LLM-based)
- ❌ Ne duplique PAS les agents existants

### **2. Complémentarité**
- **Agents**: Orchestration métier, décisions, routing
- **RAG Pipeline**: Intelligence sémantique, retrieval, ranking

### **3. KB Data**
- Préparation: Responsabilité **Data Prep Team**
- Format: Chunks avec metadata (category, section, source)
- Intégration: Une ligne: `rag.add_documents(chunks)`

### **4. Configuration**
Tous les paramètres RAG sont configurables:
```python
# Environment ou programmatique
config = PipelineConfig(
    embedding_model="all-MiniLM-L6-v2",
    vector_store_type="chroma",
    ranker_type="hybrid",
    context_target_tokens=2000,
    retriever_top_k=5
)
```

### **5. Feedback Loop**
Le système supporte les boucles de feedback:
```
Attempt 1: Query → RAG → Confidence 0.45 → Escalade
Attempt 2: Query (reformulated) → RAG → Confidence 0.75 → Répondre
```

---

## 🎉 Conclusion

Le **RAG Pipeline est conçu pour s'intégrer naturellement** dans votre processus métier:

✅ **Couvre les étapes critiques**: Analyse sémantique, recherche KB, ranking, generation  
✅ **Complément aux agents**: Ajoute intelligence IA à l'orchestration existante  
✅ **Non-breaking**: Peut coexister avec agents existants  
✅ **Configurable**: Adapté à votre contexte  
✅ **Mesurable**: Métriques intégrées à chaque étape  

**Next step**: Intégrer RAG dans `agents/orchestrator.py` pour automatiser étapes 2-4 du processus.
