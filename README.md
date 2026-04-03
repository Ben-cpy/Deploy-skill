# vLLM Skills

A collection of skills for deploying and benchmarking vLLM. This project follows the [anthropics/skills](https://github.com/anthropics/skills) template format and is installable as a Claude Code plugin marketplace.

## Overview

This repository provides modular, reusable agent skills required to operate and benchmark vLLM, following the Anthropics `SKILL.md` specification. Each skill is a self-contained directory implementing automation, scripts, and metadata for a specific operational task.

## Skills Index

| Skill | Description |
|-------|-------------|
| [vllm-deploy-docker](plugins/vllm-skills/skills/vllm-deploy-docker/) | Deploy vLLM using Docker (pre-built images or build-from-source) with NVIDIA GPU support and run the OpenAI-compatible server. |
| [vllm-deploy-k8s](plugins/vllm-skills/skills/vllm-deploy-k8s/) | Deploy vLLM to Kubernetes with GPU support, health probes, and OpenAI-compatible API endpoint. |
| [vllm-deploy-simple](plugins/vllm-skills/skills/vllm-deploy-simple/) | Quick install and deploy vLLM, start serving with a simple LLM, and test OpenAI API. |
| [vllm-prefix-cache-bench](plugins/vllm-skills/skills/vllm-prefix-cache-bench/) | Benchmark the efficiency of vLLM automatic prefix caching using fixed prompts, real datasets, or synthetic prefix/suffix patterns. |
| [vllm-bench-random-synthetic](plugins/vllm-skills/skills/vllm-bench-random-synthetic/) | Run vLLM performance benchmark using synthetic random data to measure throughput, TTFT, TPOT, and other key performance metrics without downloading external datasets. |
| [vllm-bench-serve](plugins/vllm-skills/skills/vllm-bench-serve/) | Benchmark vLLM or OpenAI-compatible serving endpoints using vllm bench serve. |

## Installation

### Plugin Marketplace (Recommended)

Install directly from the plugin marketplace in Claude Code:

```shell
/plugin marketplace add vllm-project/vllm-skills
/plugin install vllm-skills@vllm-skills
```

### Manual Install

Clone the repository and copy skills to your Claude Code skills directory:

```bash
git clone https://github.com/vllm-project/vllm-skills.git
cd vllm-skills
```

Copy to global skill folder:

```bash
cp -r plugins/vllm-skills/skills/vllm-deploy-simple ~/.claude/skills/
```

Or copy to the project skill folder:

```bash
cp -r plugins/vllm-skills/skills/vllm-deploy-simple .claude/skills/
```

## Usage

Once installed, use the skills with slash commands or natural language:

```
/vllm-deploy-simple
```

```
Deploy vLLM with Qwen2.5-1.5B-Instruct on port 8000
```

```
Install and start a vLLM server using the vllm-deploy-simple skill
```

## Supported Models

See [vLLM documentation](https://docs.vllm.ai/en/stable/models/supported_models.html) for the full list.

## Contributing

This project follows the [anthropics/skills](https://github.com/anthropics/skills) template. When adding new skills:

1. Create a new directory under `plugins/vllm-skills/skills/` (e.g., `plugins/vllm-skills/skills/your-skill/`)
2. Add a `SKILL.md` file with YAML frontmatter:
   ```yaml
   ---
   name: your-skill
   description: Brief description of what this skill does
   ---
   ```
3. Add optional `scripts/`, `references/`, and `assets/` directories
4. Update this README with your skill documentation

## License

Licensed under the Apache License 2.0. See [LICENSE](LICENSE).

## Resources

- [vLLM Documentation](https://docs.vllm.ai/)
- [vLLM GitHub](https://github.com/vllm-project/vllm)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [anthropics/skills Template](https://github.com/anthropics/skills)
