# TEAM 3 Evaluation Infrastructure - Integration Guide

## System Overview

The evaluation infrastructure for TEAM 3 consists of three main components:

### 1. **evaluation_script.py** - Core Evaluation Engine
The main script that processes questions through the agent system.

**Key Features:**
- Multi-stage processing pipeline (KB → Agents → Fallback)
- Graceful degradation when modules unavailable
- Intelligent fallback responses
- Full error handling and logging
- Matches exact required JSON format

**Usage:**
```bash
python evaluation_script.py <input_file.json> [output_file.json]
```

### 2. **quick_start.py** - Interactive Guide
Interactive menu-driven script for quick evaluation setup.

**Features:**
- Menu-based interface
- Create custom question files
- View existing results
- Run evaluations

**Usage:**
```bash
python quick_start.py
```

### 3. **batch_evaluation.py** - Batch Processing
Process multiple question files and combine results.

**Usage:**
```bash
python batch_evaluation.py file1.json file2.json file3.json
python batch_evaluation.py file1.json file2.json --output results.json
```

## Input Format

All evaluation scripts expect questions in this format:

```json
{
  "Questions": [
    {
      "id": "Q001",
      "query": "your question here"
    },
    {
      "id": "Q002",
      "query": "another question"
    }
  ]
}
```

## Output Format

All evaluation scripts return answers in this format:

```json
{
  "Team": "TEAM 3",
  "Answers": [
    {
      "id": "Q001",
      "answer": "your answer to Q001"
    },
    {
      "id": "Q002",
      "answer": "your answer to Q002"
    }
  ]
}
```
## Running Evaluations

### Single File Evaluation

```bash
# Basic
python evaluation_script.py questions_team3.json

# Custom output name
python evaluation_script.py questions_team3.json my_results.json

# From parent directory
python ai/evaluation_script.py ai/questions_team3.json
```

### Interactive Evaluation

```bash
python quick_start.py
# Then choose option and follow prompts
```

### Batch Evaluation

```bash
# Process multiple files
python batch_evaluation.py questions1.json questions2.json questions3.json

# With custom output name
python batch_evaluation.py q1.json q2.json --output combined_results.json
```

## Results Files

### Single Evaluation Output
- **Filename:** `results_TEAM3_YYYYMMDD_HHMMSS.json`
- **Location:** `ai/` folder
- **Format:** Exact JSON specification

### Batch Evaluation Output
- **Filename:** `batch_results_TEAM3_YYYYMMDD_HHMMSS.json`
- **Location:** `ai/` folder
- **Format:** Extended format with metadata

## Monitoring and Logging

The evaluation script provides real-time logging:

```
2025-12-23 04:52:51,078 - INFO - TEAM 3 - Evaluation Pipeline
2025-12-23 04:52:51,082 - INFO - ✓ Loaded input file: questions_team3.json
2025-12-23 04:52:51,084 - INFO - Processing 4 questions...
2025-12-23 04:52:51,084 - INFO - ✓ Q001 answered with fallback
...
```

**Log Levels:**
- `INFO` - Normal operation progress
- `WARNING` - Non-critical issues (missing modules)
- `ERROR` - Critical failures (file not found)
- `DEBUG` - Detailed technical info (use for troubleshooting)

## Performance Characteristics

### Speed
- **Per question:** ~50-100ms (without KB/agents)
- **With KB:** ~200-500ms depending on similarity search
- **With Agents:** ~500-2000ms depending on processing complexity

### Example Runtime
- 4 questions: ~200ms (fallback only)
- 4 questions: ~1-2s (with KB enabled)
- 4 questions: ~2-8s (with full agent processing)