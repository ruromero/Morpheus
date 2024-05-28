# SPDX-FileCopyrightText: Copyright (c) 2023-2024, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from unittest import mock

import cudf

from _utils import assert_results
from _utils.llm import mk_mock_ollama_response
from _utils.llm import mk_mock_openai_response
from morpheus.config import Config
from morpheus.llm import LLMEngine
from morpheus.llm.nodes.extracter_node import ExtracterNode
from morpheus.llm.nodes.llm_generate_node import LLMGenerateNode
from morpheus.llm.services.llm_service import LLMService
from morpheus.llm.services.nemo_llm_service import NeMoLLMService
from morpheus.llm.services.ollama_llm_service import OllamaLLMService
from morpheus.llm.services.openai_chat_service import OpenAIChatService
from morpheus.llm.task_handlers.simple_task_handler import SimpleTaskHandler
from morpheus.messages import ControlMessage
from morpheus.pipeline.linear_pipeline import LinearPipeline
from morpheus.stages.input.in_memory_source_stage import InMemorySourceStage
from morpheus.stages.llm.llm_engine_stage import LLMEngineStage
from morpheus.stages.output.compare_dataframe_stage import CompareDataFrameStage
from morpheus.stages.preprocess.deserialize_stage import DeserializeStage


def _build_engine(llm_service_cls: type[LLMService]):
    llm_service = llm_service_cls()
    llm_clinet = llm_service.get_client(model_name="test_model")

    engine = LLMEngine()
    engine.add_node("extracter", node=ExtracterNode())
    engine.add_node("completion", inputs=["/extracter"], node=LLMGenerateNode(llm_client=llm_clinet))
    engine.add_task_handler(inputs=["/completion"], handler=SimpleTaskHandler())

    return engine


def _run_pipeline(config: Config,
                  llm_service_cls: type[LLMService],
                  country_prompts: list[str],
                  capital_responses: list[str]):
    """
    Loosely patterned after `examples/llm/completion`
    """
    source_df = cudf.DataFrame({"prompt": country_prompts})
    expected_df = cudf.DataFrame({"prompt": country_prompts, "response": capital_responses})

    completion_task = {"task_type": "completion", "task_dict": {"input_keys": ["prompt"]}}

    pipe = LinearPipeline(config)

    pipe.set_source(InMemorySourceStage(config, dataframes=[source_df]))

    pipe.add_stage(
        DeserializeStage(config, message_type=ControlMessage, task_type="llm_engine", task_payload=completion_task))

    pipe.add_stage(LLMEngineStage(config, engine=_build_engine(llm_service_cls)))
    sink = pipe.add_stage(CompareDataFrameStage(config, compare_df=expected_df))

    pipe.run()

    assert_results(sink.get_results())


def test_completion_pipe_nemo(config: Config,
                              mock_nemollm: mock.MagicMock,
                              country_prompts: list[str],
                              capital_responses: list[str]):
    mock_nemollm.post_process_generate_response.side_effect = [{"text": response} for response in capital_responses]
    _run_pipeline(config, NeMoLLMService, country_prompts, capital_responses)


def test_completion_pipe_openai(config: Config,
                                mock_chat_completion: tuple[mock.MagicMock, mock.MagicMock],
                                country_prompts: list[str],
                                capital_responses: list[str]):
    (mock_client, mock_async_client) = mock_chat_completion
    mock_async_client.chat.completions.create.side_effect = [
        mk_mock_openai_response([response]) for response in capital_responses
    ]

    _run_pipeline(config, OpenAIChatService, country_prompts, capital_responses)

    mock_client.chat.completions.create.assert_not_called()
    mock_async_client.chat.completions.create.assert_called()


def test_completion_pipe_ollama(config: Config,
                                mock_ollama: tuple[mock.MagicMock, mock.MagicMock],
                                country_prompts: list[str],
                                capital_responses: list[str]):
    (mock_client, mock_async_client) = mock_ollama
    mock_async_client.generate = [
        mk_mock_ollama_response([response]) for response in capital_responses
    ]

    _run_pipeline(config, OllamaLLMService, country_prompts, capital_responses)

    mock_client.generate.assert_not_called()
    mock_async_client.generate.assert_called()
