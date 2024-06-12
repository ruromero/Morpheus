import logging

from morpheus.config import Config
from morpheus.pipeline import LinearPipeline
from morpheus.stages.general.monitor_stage import MonitorStage
from morpheus.stages.input.http_server_source_stage import HttpServerSourceStage
from morpheus.stages.general.monitor_stage import MonitorStage
from morpheus.stages.general.trigger_stage import TriggerStage
from morpheus.stages.inference.triton_inference_stage import TritonInferenceStage
from morpheus.stages.output.write_to_vector_db_stage import WriteToVectorDBStage
from morpheus.stages.preprocess.preprocess_nlp_stage import PreprocessNLPStage
from morpheus.utils.logger import configure_logging
from utils import default_vdb_config
from utils import defaultNLP_config
from utils import default_triton_config

def run_pipeline():
    # Enable the Morpheus logger
    configure_logging(log_level=logging.DEBUG)

    config = Config()

    pipeline = LinearPipeline(config)

    pipeline.set_source(HttpServerSourceStage(config, bind_address="0.0.0.0"))

    pipeline.add_stage(MonitorStage(config))
    pipeline.add_stage(PreprocessNLPStage(config, defaultNLP_config()))

    pipeline.add_stage(
        MonitorStage(config, description="Tokenize rate", unit='events', delayed_start=True))

    pipeline.add_stage(TritonInferenceStage(config, default_triton_config()))

    pipeline.add_stage(
        MonitorStage(config, description="Inference rate", unit="events", delayed_start=True))

    pipeline.add_stage(WriteToVectorDBStage(config, default_vdb_config()))

    pipeline.add_stage(
        MonitorStage(config, description="Upload rate", unit="events", delayed_start=True))

    pipeline.run()

if __name__ == "__main__":
    run_pipeline()
