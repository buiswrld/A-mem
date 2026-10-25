# Vendored A-MEM

This directory contains the A-MEM implementation used by the research harness,
with local adaptations for controlled memory evolution. It is tracked source,
not a Git submodule. Use the repository root environment and reproduction
instructions; this directory's packaging files describe the upstream library.

- Upstream paper: [A-MEM: Agentic Memory for LLM Agents](https://arxiv.org/abs/2502.12110)
- Upstream experiment repository: [AgenticMemory](https://github.com/WujiangXu/AgenticMemory)
- License: [MIT, copyright 2025 AGI Research](LICENSE)

The harness integration lives in `harness/memory.py` and
`harness/llm_backend.py` at the repository root. Upstream tests remain under
`tests/`; the study's controlled evolution tests are in
`harness/tests/test_amem_v2.py`.
