from langgraph.graph import StateGraph, END
from backend.agents.state import AgentState
from backend.agents import (
    query_classifier,
    legal_retriever,
    legal_analyzer,
    fact_checker,
    response_generator
)

def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("classify", query_classifier.run)
    graph.add_node("retrieve", legal_retriever.run)
    graph.add_node("analyze", legal_analyzer.run)
    graph.add_node("fact_check", fact_checker.run)
    graph.add_node("generate", response_generator.run)

    # Add edges
    graph.set_entry_point("classify")
    graph.add_edge("classify", "retrieve")
    graph.add_edge("retrieve", "analyze")
    graph.add_edge("analyze", "fact_check")
    graph.add_edge("fact_check", "generate")
    graph.add_edge("generate", END)

    return graph.compile()
