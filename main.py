"""
Main entry point — starts the FastAPI server with uvicorn.

Usage:
  python main.py
"""

import uvicorn
from app.config import HOST, PORT


def main():
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║             🏛️  Vietnamese Legal AI Agent  🏛️               ║
║                                                              ║
║  Server starting at http://{HOST}:{PORT}                     ║
║                                                              ║
║  IMPORTANT:                                                  ║
║  Before first run, ingest data:                              ║
║    python -m app.ingest --max-docs 2000                      ║
║                                                              ║
║  Set your OpenAI API key in .env:                            ║
║    OPENAI_API_KEY=sk-your-key-here                           ║
╚══════════════════════════════════════════════════════════════╝
""")

    uvicorn.run(
        "app.server:app",
        host=HOST,
        port=PORT,
        reload=True,
        log_level="info",
    )


if __name__ == "__main__":
    main()
