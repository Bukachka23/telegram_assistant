#!/usr/bin/env python3
import json
import sys


def main():
    payload = json.loads(sys.argv[1])
    tool_name = payload["tool"]
    args = payload.get("args", {})

    # Map extension param names to library param names
    if "repo_path" in args:
        args["repo_root"] = args.pop("repo_path")

    if tool_name == "build_or_update_graph":
        from code_review_graph.tools import build_or_update_graph
        result = build_or_update_graph(**args)

    elif tool_name == "get_impact_radius":
        from code_review_graph.tools import get_impact_radius
        result = get_impact_radius(**args)

    elif tool_name == "get_review_context":
        from code_review_graph.tools import get_review_context
        result = get_review_context(**args)

    elif tool_name == "query_graph":
        from code_review_graph.tools import query_graph
        # Map extension params to library params
        if "symbol" in args and "symbol" not in args.get("pattern", ""):
            pattern = args.pop("symbol")
            query_type = args.pop("query_type", "callers")
            args["pattern"] = pattern
            args["target"] = query_type
        result = query_graph(**args)

    elif tool_name == "semantic_search_nodes":
        from code_review_graph.tools import semantic_search_nodes
        # Map top_k -> limit
        if "top_k" in args:
            args["limit"] = args.pop("top_k")
        result = semantic_search_nodes(**args)

    elif tool_name == "list_graph_stats":
        from code_review_graph.tools import list_graph_stats
        result = list_graph_stats(**args)

    else:
        result = {"error": f"Unknown tool: {tool_name}"}

    print(json.dumps(result) if isinstance(result, dict) else str(result))


if __name__ == "__main__":
    main()
