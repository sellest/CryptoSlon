# rag/pipeline.py
from typing import Dict

class RAGPipeline:
    def __init__(self, prep, retrieval, reranker, packer, prompter, generator, guardrails, logger):
        self.prep = prep
        self.retrieval = retrieval
        self.reranker = reranker
        self.packer = packer
        self.prompter = prompter
        self.generator = generator
        self.guard = guardrails
        self.log = logger

    def run(self, raw_query: str, system_prompt: str, cite: bool = True) -> Dict:
        log = {"query": raw_query, "stages": {}}

        qr = self.prep.run(raw_query)
        log["stages"]["query_prep"] = {"language": qr.language, "rewritten": qr.rewritten, "entities": qr.entities}

        docs20 = self.retrieval.run(qr.rewritten or raw_query, k=20)
        log["stages"]["retrieval"] = {"count": len(docs20), "doc_ids": [d.metadata.get("id") for d in docs20]}

        docs7 = self.reranker.run(qr.rewritten or raw_query, docs20, top_k=7)
        log["stages"]["rerank"] = {"count": len(docs7), "doc_ids": [d.metadata.get("id") for d in docs7]}

        guard = self.guard.check(raw_query, docs7, scores=[d.metadata.get("score", 0) for d in docs7])
        if not guard.get("ok", True):
            self.log.log({**log, "guardrails": guard})
            return {"answer": "Недостаточно контекста для уверенного ответа. Уточни, пожалуйста, детали вопроса.", "sources": [], "guardrails": guard}

        ctx = self.packer.run(docs7)
        prompt = self.prompter.build(question=raw_query, ctx=ctx, system_prompt=system_prompt, cite=cite)
        answer = self.generator.run(prompt)

        result = {
            "answer": answer,
            "sources": ctx.get("citations", []),
            "debug": {"query_prep": log["stages"]["query_prep"]}
        }
        self.log.log({**log, "success": True, "sources": result["sources"]})
        return result
