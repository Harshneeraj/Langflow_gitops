"""Custom Langflow component for LiteLLM proxy integration.

Drop this file into your Langflow components directory
(LANGFLOW_COMPONENTS_PATH) to make the LiteLLM component available
in the flow builder.

The component fetches the available model list dynamically from the
LiteLLM proxy's /models endpoint, so you don't need to hard-code model
names.

Usage:
    1. Set API Base URL to your LiteLLM proxy (e.g. http://litellm-service:4000)
    2. Set API Key to your LiteLLM master key
    3. Click the refresh button on the Model dropdown to load available models
"""
from langchain_community.chat_models.litellm import ChatLiteLLM, ChatLiteLLMException
from langflow.base.constants import STREAM_INFO_TEXT
from langflow.base.models.model import LCModelComponent
from langflow.field_typing import LanguageModel
from langflow.io import (
    BoolInput,
    DictInput,
    DropdownInput,
    FloatInput,
    IntInput,
    MessageInput,
    SecretStrInput,
    StrInput,
)


class ChatLiteLLMModelComponent(LCModelComponent):
    display_name = "LiteLLM"
    description = "Connect to any LLM via a LiteLLM proxy server."
    documentation = "https://python.langchain.com/docs/integrations/chat/litellm"
    icon = "🚄"

    inputs = [
        MessageInput(name="input_value", display_name="Input"),
        StrInput(
            name="api_base",
            display_name="API Base URL",
            required=False,
            info="LiteLLM proxy URL. Example: http://litellm-service:4000",
        ),
        SecretStrInput(
            name="api_key",
            display_name="API Key",
            required=False,
        ),
        DropdownInput(
            name="model",
            display_name="Model",
            options=[""],
            required=True,
            info="Click the refresh button to load models from the proxy.",
            refresh_button=True,
            real_time_refresh=True,
        ),
        FloatInput(
            name="temperature",
            display_name="Temperature",
            value=0.7,
        ),
        IntInput(
            name="max_tokens",
            display_name="Max Tokens",
            value=256,
            info="Maximum number of tokens to generate.",
        ),
        FloatInput(name="top_p", display_name="Top P", advanced=True, value=0.5),
        IntInput(name="top_k", display_name="Top K", advanced=True, value=35),
        IntInput(name="n", display_name="N", advanced=True, value=1,
                 info="Number of completions to generate per prompt."),
        IntInput(name="max_retries", display_name="Max Retries", advanced=True, value=6),
        DictInput(name="kwargs", display_name="Extra Kwargs", advanced=True, is_list=True, value={}),
        DictInput(name="model_kwargs", display_name="Model Kwargs", advanced=True, is_list=True, value={}),
        BoolInput(name="verbose", display_name="Verbose", advanced=True, value=False),
        BoolInput(name="stream", display_name="Stream", info=STREAM_INFO_TEXT, advanced=True),
        StrInput(name="system_message", display_name="System Message", advanced=True),
    ]

    def build_model(self) -> LanguageModel:
        try:
            import litellm
            litellm.drop_params = True
            litellm.set_verbose = self.verbose
        except ImportError as e:
            raise ChatLiteLLMException(
                "litellm is not installed. Run: pip install litellm"
            ) from e

        # Remove empty keys from dicts
        kwargs = {k: v for k, v in self.kwargs.items() if k}
        model_kwargs = {k: v for k, v in self.model_kwargs.items() if k}

        if "api_base" not in kwargs:
            raise ValueError("api_base is required in Extra Kwargs")
        if "api_version" not in model_kwargs:
            raise ValueError("api_version is required in Model Kwargs")

        model = ChatLiteLLM(
            model=self.model,
            streaming=self.stream,
            temperature=self.temperature,
            model_kwargs=model_kwargs,
            top_p=self.top_p,
            top_k=self.top_k,
            n=self.n,
            max_tokens=self.max_tokens,
            max_retries=self.max_retries,
            **kwargs,
        )
        model.client.api_key = self.api_key
        return model

    def update_build_config(self, build_config, field_value, field_name=None):
        """Dynamically populate the model dropdown from the LiteLLM proxy."""
        if field_name == "model":
            import requests
            url = f"{self.api_base.rstrip('/')}/models"
            headers = {
                "accept": "application/json",
                "x-litellm-api-key": self.api_key,
            }
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()
            models = [m["id"] for m in response.json().get("data", [])]
            build_config["model"]["options"] = models
            if models:
                build_config["model"]["value"] = models[0]
        return build_config
