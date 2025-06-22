# Diary RAG System

  * [ ] A local Retrieval-Augmented Generation (RAG) system for querying your personal diary files using Ollama. Ask questions about your life, memories, and experiences across all your diary entries with natural language queries.

## Features

- 🔍 **Semantic Search**: Find relevant diary entries using natural language queries
- 🤖 **Local AI**: Uses Ollama for private, offline AI responses
- 📅 **Date-Aware**: Automatically extracts and indexes dates from diary files
- 🧠 **Smart Chunking**: Splits long diary entries for better retrieval accuracy
- 💾 **Persistent Index**: SQLite database stores embeddings for fast subsequent queries
- 🔒 **Privacy First**: Everything runs locally - your diary stays on your machine
- 📝 **Flexible Formats**: Supports various date formats and file organizations

## Quick Start

### Prerequisites

- Python 3.8+
- [Ollama](https://ollama.ai/) installed and running locally
- Poetry (recommended) or pip for dependency management

### Installation

#### With Poetry (Recommended)

```bash
# Clone or create your project directory
git clone <your-repo> diary-rag
cd diary-rag

# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

#### With pip

```bash
pip install sentence-transformers requests numpy
```

### Setup Ollama

```bash
# Install and start Ollama
ollama serve

# Pull a model (choose one)
ollama pull llama2        # Smaller, faster
ollama pull llama2:13b    # Larger, more capable
ollama pull mistral       # Alternative option
```

## Usage

### Command Line Interface

#### 1. Initialize the Database (Optional)

For first-time setup, initialize the database schema:

```bash
# With Poetry
diary-rag /path/to/your/diary/files --init-db

# Or directly with Python
python src/diary_rag/main.py /path/to/your/diary/files --init-db
```

#### 2. Build the Index

Create an embedding index of your diary files:

```bash
# With Poetry
diary-rag /path/to/your/diary/files --build

# Or directly with Python
python src/diary_rag/main.py /path/to/your/diary/files --build
```

#### 3. Query Your Diary

Ask questions about your diary entries:

```bash
# Simple query
diary-rag /path/to/your/diary/files --query "What did I do last weekend?"

# More complex queries
diary-rag /path/to/your/diary/files --query "How was I feeling about work in March?"
diary-rag /path/to/your/diary/files --query "What books did I mention reading?"
```

#### 3. Interactive Mode

For ongoing conversations:

```bash
diary-rag /path/to/your/diary/files
# Then type your questions interactively
```

#### 4. List Indexed Entries

See what diary entries are in your index:

```bash
diary-rag /path/to/your/diary/files --list
```

### Advanced Options

```bash
# Use a different Ollama model
diary-rag /path/to/diary --query "your question" --model mistral

# Force rebuild the index (if you've added new diary files)
diary-rag /path/to/diary --rebuild

# Initialize the database (without building the index)
diary-rag /path/to/diary --init-db

# Get help
diary-rag --help
```

## File Organization

The system automatically detects dates from your diary filenames. Supported formats:

- `2024-01-15.txt` (YYYY-MM-DD)
- `20240115.txt` (YYYYMMDD)
- `01-15-2024.txt` (MM-DD-YYYY)
- `diary_2024-01-15.txt` (with prefix)
- `2024/01/15.txt` (in subdirectories)

### Example Directory Structure

```
diary-files/
├── 2024-01-01.txt
├── 2024-01-02.txt
├── 2024-01-03.txt
└── ...
```

Or with org files:
```
org-roam-dailies/
├── 2024-01-01.org
├── 2024-01-02.org
├── 2024-01-03.org
└── ...
```

## Example Queries

Here are some example questions you can ask your diary:

### Memory and Events
- "What did I do for my birthday last year?"
- "Tell me about my vacation in July"
- "What concerts or events did I attend?"

### Emotions and Reflections
- "How was I feeling about my job in March?"
- "What was I worried about last month?"
- "When did I feel most happy or excited?"

### Relationships and Social
- "What did I write about Sarah recently?"
- "Tell me about dinner parties I hosted"
- "How did my relationships change this year?"

### Goals and Progress
- "What goals did I set at the beginning of the year?"
- "How is my fitness journey going?"
- "What books have I been reading?"

### Health and Habits
- "How has my sleep been lately?"
- "What healthy habits did I mention?"
- "When did I last write about feeling sick?"

## Configuration

### Customizing the System

You can modify the system behavior by editing the `DiaryRAG` class initialization:

```python
rag = DiaryRAG(
    diary_dir="/path/to/diary",
    embedding_model="all-MiniLM-L6-v2",  # Change for different embeddings
    ollama_model="llama2",                # Change Ollama model
    chunk_size=500,                       # Adjust text chunk size
    overlap=50                            # Overlap between chunks
)
```

### Embedding Models

Available embedding models (via sentence-transformers):
- `all-MiniLM-L6-v2` - Fast, good quality (default)
- `all-mpnet-base-v2` - Higher quality, slower
- `paraphrase-MiniLM-L6-v2` - Good for paraphrasing

### Ollama Models

Popular Ollama models:
- `llama2` - Fast, good for most queries
- `llama2:13b` - More capable, slower
- `mistral` - Alternative with good performance
- `codellama` - If your diary contains code

## Integration with Org-Mode

If you use Emacs org-mode for journaling, see the included `org_journal_converter.py` script to convert org-journal files to org-roam-dailies format compatible with this RAG system.

## Privacy and Security

- **Local Processing**: All data stays on your machine
- **No Cloud Services**: Uses local Ollama instance
- **Encrypted Storage**: Consider encrypting your diary files at rest
- **Access Control**: Ensure proper file permissions on diary directory

## Performance Tips

- **SSD Storage**: Store embeddings database on SSD for faster queries
- **RAM**: More RAM allows larger models and faster processing
- **GPU**: Some embedding models can use GPU acceleration
- **Chunk Size**: Smaller chunks (300-500 words) often work better than large ones

## Troubleshooting

### Common Issues

**"Connection refused" error:**
- Ensure Ollama is running: `ollama serve`
- Check if Ollama is on port 11434: `curl http://localhost:11434/api/tags`

**"No relevant diary entries found":**
- Rebuild the index: `--rebuild`
- Check if your diary files are in supported formats
- Try more specific or different query terms

**Slow queries:**
- Use a smaller embedding model
- Reduce chunk size
- Use a faster Ollama model

**Poor answer quality:**
- Try a larger Ollama model (`llama2:13b` instead of `llama2`)
- Increase the number of retrieved chunks
- Make your queries more specific

### Getting Help

1. Check that your diary files are readable and in supported date formats
2. Verify Ollama is running and accessible
3. Try rebuilding the index with `--rebuild`
4. Test with simple queries first

## Development

### Project Structure

```
diary-rag/
├── pyproject.toml          # Poetry configuration
├── README.md              # This file
├── src/
│   └── diary_rag/
│       ├── __init__.py
│       └── main.py        # Main RAG system
├── scripts/
│   └── org_journal_converter.py  # Org-mode conversion
└── tests/
    └── test_diary_rag.py  # Tests
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run linting: `poetry run black src/ && poetry run flake8 src/`
6. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- Built on [sentence-transformers](https://www.sbert.net/) for embeddings
- Uses [Ollama](https://ollama.ai/) for local LLM inference
- Inspired by the need for private, personal AI assistants
