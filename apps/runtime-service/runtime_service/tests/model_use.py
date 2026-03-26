from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from langchain_core.messages import HumanMessage

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from runtime_service.conf.settings import require_model_spec  # noqa: E402
from runtime_service.runtime.modeling import (  # noqa: E402
    apply_model_runtime_params,
    resolve_model,
)
from runtime_service.runtime.options import AppRuntimeConfig, ModelSpec  # noqa: E402


def build_iflow_deepseek_v3_options() -> AppRuntimeConfig:
    resolved_model_id, raw_spec = require_model_spec("iflow_deepseek-v3")
    return AppRuntimeConfig(
        environment="test",
        model_id=resolved_model_id,
        model_spec=ModelSpec(
            model_provider=raw_spec["model_provider"],
            model=raw_spec["model"],
            base_url=raw_spec["base_url"],
            api_key=raw_spec["api_key"],
        ),
        temperature=0.2,
        max_tokens=512,
        top_p=0.95,
    )


async def run_iflow_deepseek_v3_case(prompt: str = "请只回复 ok") -> str:
    options = build_iflow_deepseek_v3_options()
    model = apply_model_runtime_params(resolve_model(options.model_spec), options)
    response = await model.ainvoke([HumanMessage(content=prompt)])
    content = getattr(response, "content", "")
    if isinstance(content, str):
        return content
    return str(content)


async def main() -> None:
    output = await run_iflow_deepseek_v3_case(prompt='你是什么模型')
    print(output)


if __name__ == "__main__":
    asyncio.run(main())
