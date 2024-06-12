import typing

import pymilvus

def defaultNLP_config():
  """"
  Sets a default configuration for the NLP integration
  """
  return {}

def default_triton_config():
  """
  Sets a default configuration for the Triton Inference Server
  """
  return {
    "model_name": "all-MiniLM-L6-v2",
    "server_url": "http://triton-server:8001"
  }

def default_vdb_config() -> typing.Dict[str, typing.Any]:
  """
  Sets a default configuration for the Vector DB connection
  """
  milvus_resource_kwargs = {
      "index_conf": {
          "field_name": "embedding",
          "metric_type": "L2",
          "index_type": "HNSW",
          "params": {
              "M": 8,
              "efConstruction": 64,
          },
      },
      "schema_conf": {
          "enable_dynamic_field": True,
          "schema_fields": [
              pymilvus.FieldSchema(name="id",
                                    dtype=pymilvus.DataType.INT64,
                                    description="Primary key for the collection",
                                    is_primary=True,
                                    auto_id=True).to_dict(),
              pymilvus.FieldSchema(name="title",
                                    dtype=pymilvus.DataType.VARCHAR,
                                    description="The title of the Vex",
                                    max_length=65_535).to_dict(),
              pymilvus.FieldSchema(name="cve",
                                    dtype=pymilvus.DataType.VARCHAR,
                                    description="The CVE tracked",
                                    max_length=65_535).to_dict(),
              pymilvus.FieldSchema(name="source",
                                    dtype=pymilvus.DataType.VARCHAR,
                                    description="The reference to the CVE source",
                                    max_length=65_535).to_dict(),
              pymilvus.FieldSchema(name="content",
                                    dtype=pymilvus.DataType.VARCHAR,
                                    description="A chunk of text from the Vex file",
                                    max_length=65_535).to_dict(),
              pymilvus.FieldSchema(name="embedding",
                                    dtype=pymilvus.DataType.FLOAT_VECTOR,
                                    description="Embedding vectors",
                                    dim=384).to_dict(),
          ],
          "description": "Vexes collection schema"
      }
      
  }
  db_config = {
    "batch_size": 16384,
    "embedding_size": 384,
    "recreate": True,
    "uri": "http://milvus-standalone:19530",
    "service": "milvus",
    "resource_name": "vexes",
    "resource_schemas": {
      "vexes": milvus_resource_kwargs
    }
  }

  return db_config