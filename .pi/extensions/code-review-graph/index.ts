import type { ExtensionAPI } from "@mariozechner/.pi-coding-agent";
import { Type } from "@sinclair/typebox";
import * as path from "node:path";
import * as url from "node:url";

const __dirname = path.dirname(url.fileURLToPath(import.meta.url));
const BRIDGE = path.join(__dirname, "bridge.py");

export default function (pi: ExtensionAPI) {

  // ── Helper ──────────────────────────────────────────────────────────────
  async function callBridge(
    tool: string,
    args: Record<string, unknown>,
    signal: AbortSignal
  ): Promise<string> {
    const payload = JSON.stringify({ tool, args });
    const res = await pi.exec("python3", [BRIDGE, payload], {
      signal,
      timeout: 120_000,
    });
    if (res.code !== 0) throw new Error(res.stderr);
    return res.stdout.trim();
  }

  // ── Tool: build_or_update_graph ─────────────────────────────────────────
  pi.registerTool({
    name: "crg_build_graph",
    label: "CRG: Build/Update Graph",
    description:
      "Build or incrementally update the persistent code-review knowledge graph for the current project. " +
      "Run this first, or after large refactors.",
    parameters: Type.Object({
      repo_path: Type.Optional(
        Type.String({ description: "Repo root path (defaults to cwd)" })
      ),
    }),
    async execute(toolCallId, params, signal, onUpdate, ctx) {
      onUpdate?.({ content: [{ type: "text", text: "Building code graph…" }] });
      const text = await callBridge(
        "build_or_update_graph",
        { repo_path: params.repo_path ?? ctx.cwd },
        signal
      );
      return { content: [{ type: "text", text }], details: {} };
    },
  });

  // ── Tool: get_impact_radius ─────────────────────────────────────────────
  pi.registerTool({
    name: "crg_impact_radius",
    label: "CRG: Impact Radius",
    description:
      "Given a list of changed files, compute the blast radius: every caller, " +
      "dependent module, and test that might be affected.",
    parameters: Type.Object({
      changed_files: Type.Array(Type.String(), {
        description: "Relative paths of changed files",
      }),
      repo_path: Type.Optional(Type.String()),
    }),
    async execute(toolCallId, params, signal, onUpdate, ctx) {
      onUpdate?.({ content: [{ type: "text", text: "Computing impact radius…" }] });
      const text = await callBridge(
        "get_impact_radius",
        {
          changed_files: params.changed_files,
          repo_path: params.repo_path ?? ctx.cwd,
        },
        signal
      );
      return { content: [{ type: "text", text }], details: {} };
    },
  });

  // ── Tool: get_review_context ────────────────────────────────────────────
  pi.registerTool({
    name: "crg_review_context",
    label: "CRG: Review Context",
    description:
      "Return the minimal, token-optimised review context (structural summary + " +
      "only the files Claude needs to read) for a given PR / diff.",
    parameters: Type.Object({
      changed_files: Type.Array(Type.String()),
      repo_path: Type.Optional(Type.String()),
    }),
    async execute(toolCallId, params, signal, onUpdate, ctx) {
      onUpdate?.({ content: [{ type: "text", text: "Fetching review context…" }] });
      const text = await callBridge(
        "get_review_context",
        {
          changed_files: params.changed_files,
          repo_path: params.repo_path ?? ctx.cwd,
        },
        signal
      );
      return { content: [{ type: "text", text }], details: {} };
    },
  });

  // ── Tool: query_graph ───────────────────────────────────────────────────
  pi.registerTool({
    name: "crg_query_graph",
    label: "CRG: Query Graph",
    description:
      "Query the graph for callers, callees, tests, imports, or inheritance " +
      "of a specific symbol.",
    parameters: Type.Object({
      symbol: Type.String({ description: "Function/class name to query" }),
      query_type: Type.String({
        description: "One of: callers | callees | tests | imports | inheritance",
      }),
      repo_path: Type.Optional(Type.String()),
    }),
    async execute(toolCallId, params, signal, onUpdate, ctx) {
      const text = await callBridge(
        "query_graph",
        {
          symbol: params.symbol,
          query_type: params.query_type,
          repo_path: params.repo_path ?? ctx.cwd,
        },
        signal
      );
      return { content: [{ type: "text", text }], details: {} };
    },
  });

  // ── Tool: semantic_search_nodes ─────────────────────────────────────────
  pi.registerTool({
    name: "crg_semantic_search",
    label: "CRG: Semantic Search",
    description:
      "Search code entities (functions, classes) by name or meaning using " +
      "vector embeddings.",
    parameters: Type.Object({
      query: Type.String({ description: "Search term or natural language description" }),
      top_k: Type.Optional(Type.Number({ description: "Max results, default 10" })),
      repo_path: Type.Optional(Type.String()),
    }),
    async execute(toolCallId, params, signal, onUpdate, ctx) {
      const text = await callBridge(
        "semantic_search_nodes",
        {
          query: params.query,
          top_k: params.top_k ?? 10,
          repo_path: params.repo_path ?? ctx.cwd,
        },
        signal
      );
      return { content: [{ type: "text", text }], details: {} };
    },
  });

  // ── Tool: list_graph_stats ──────────────────────────────────────────────
  pi.registerTool({
    name: "crg_graph_stats",
    label: "CRG: Graph Stats",
    description: "Show graph size, node/edge counts, and health metrics.",
    parameters: Type.Object({
      repo_path: Type.Optional(Type.String()),
    }),
    async execute(toolCallId, params, signal, onUpdate, ctx) {
      const text = await callBridge(
        "list_graph_stats",
        { repo_path: params.repo_path ?? ctx.cwd },
        signal
      );
      return { content: [{ type: "text", text }], details: {} };
    },
  });

  // ── Convenience command ─────────────────────────────────────────────────
  pi.registerCommand("crg-build", {
    description: "Build or refresh the .code-review-graph for this project",
    handler: async (_args, ctx) => {
      ctx.ui.notify("Building code graph…", "info");
      const res = await pi.exec("python3", [BRIDGE, JSON.stringify({ tool: "build_or_update_graph", args: { repo_path: ctx.cwd } })], {});
      ctx.ui.notify(res.code === 0 ? "Graph ready ✓" : `Error: ${res.stderr}`, res.code === 0 ? "success" : "error");
    },
  });
}