# Copyright (c) 2023-2024, NVIDIA CORPORATION.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import os

import ollama

from morpheus.llm.services.llm_service import LLMClient
from morpheus.llm.services.llm_service import LLMService

logger = logging.getLogger(__name__)

IMPORT_EXCEPTION = None
IMPORT_ERROR_MESSAGE = (
    "OllamaLLM not found. Install it and other additional dependencies by running the following command:\n"
    "`pip install ollama`")

try:
    from ollama import AsyncClient
    from ollama import Client
except ImportError as import_exc:
    IMPORT_EXCEPTION = import_exc


class OllamaLLMClient(LLMClient):
    """
    Client for interacting with a specific model in Ollama. This class should be constructed with the
    `OllamaLLMService.get_client` method.

    Parameters
    ----------
    parent : OllamaLLMService
        The parent service for this client.
    model_name : str
        The name of the model to interact with.

    model_kwargs : dict[str, typing.Any]
        Additional keyword arguments to pass to the model when generating text.
    """

    def __init__(self, parent: "OllamaLLMService", *, model_name: str, **model_kwargs) -> None:
        if IMPORT_EXCEPTION is not None:
            raise ImportError(IMPORT_ERROR_MESSAGE) from IMPORT_EXCEPTION

        super().__init__()

        assert parent is not None, "Parent service cannot be None."

        self._parent = parent
        self._model_name = model_name
        self._model_kwargs = model_kwargs
        self._prompt_key = "prompt"

        host = os.environ.get("OLLAMA_HOST", 'http://localhost:11434')

        self._client = Client(host=host)
        self._async_client = AsyncClient(host=host, )

    def get_input_names(self) -> list[str]:
        return [self._prompt_key]

    def generate(self, **input_dict) -> str:
        """
        Issue a request to generate a response based on a given prompt.

        Parameters
        ----------
        input_dict : dict
            Input containing prompt data.
        """
        output = self._client.generate(model=self._model_name, prompt=input_dict[self._prompt_key])
        return self._extract_completion(output)

    async def generate_async(self, **input_dict) -> str:
        """
        Issue an asynchronous request to generate a response based on a given prompt.

        Parameters
        ----------
        input_dict : dict
            Input containing prompt data.
        """
        output = await self._async_client.generate(model=self._model_name, prompt=input_dict[self._prompt_key])
        return self._extract_completion(output)

    def _extract_completion(self, output: ollama._types.GenerateResponse) -> str:
        return output['response']


class OllamaLLMService(LLMService):
    """
    A service for interacting with Ollama LLM models, this class should be used to create a client for a specific model.
    """

    def __init__(self, *, retry_count=5) -> None:
        """
        Creates a service for interacting with Ollama LLM models.

        Parameters
        ----------
        retry_count : int, optional
            The number of times to retry a request before raising an exception, by default 5

        """

        if IMPORT_EXCEPTION is not None:
            raise ImportError(IMPORT_ERROR_MESSAGE) from IMPORT_EXCEPTION

        super().__init__()

        self._retry_count = retry_count

    def get_client(self, *, model_name: str, **model_kwargs) -> OllamaLLMClient:
        """
        Returns a client for interacting with a specific model. This method is the preferred way to create a client.

        Parameters
        ----------
        model_name : str
            The name of the model to create a client for.

        model_kwargs : dict[str, typing.Any]
            Additional keyword arguments to pass to the model when generating text.
        """

        return OllamaLLMClient(self, model_name=model_name, **model_kwargs)
