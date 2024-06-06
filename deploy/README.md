# Deploy on OpenShift

# Morpheus

Deploy Morpheus as root. Grant to run as anyuid

```bash
oc create sa morpheus-sa
oc adm policy add-scc-to-user anyuid -z morpheus-sa
```

## Build Morpheus

You can create a Build that prepares the `conda` environment and 
creates an imageStreamTag `morpheus:latest` in your namespace.

This step takes time but saves you a lot of time later on.

```bash
oc apply -f deploy/morpheus-build-config.yaml
oc start-build --from-build=morpheus-build
```

## Deploy morpheus

There is a template that creates a deployment for Morpheus. It defaults to `nvcr.io/nvidia/morpheus/morpheus:v24.03.02-runtime`
But if you used the BuildConfig you can override the `CONTAINER_IMAGE` parameter with the imageStreamTag.

```bash
oc process -f deploy/morpheus-template.yaml -p CONTAINER_IMAGE=image-registry.openshift-image-registry.svc:5000/`oc project -q`/morpheus:latest
```

## Access the pod

```bash
oc exec -it `oc get po -l app=morpheus -o=name` -- bash
```

Update the conda environment. **Skip if you are using the image from the Build.**

```bash
mamba env update \
  -n ${CONDA_DEFAULT_ENV} \
  --file ./conda/environments/all_cuda-121_arch-x86_64.yaml
python examples/developer_guide/1_simple_python_stage/run.py
```

Run the example:

```bash
python examples/llm/main.py vdb_upload pipeline --enable_cache --enable_monitors --embedding_model_name all-MiniLM-L6-v2 --triton_server_url=triton-server:8001 --vector_db_uri=http://milvus-standalone:19530
```

**Note**: In the [./examples/llm](../examples/llm/) folder you will find updated versions allowing to communicate with an external vector DB.

## Triton Server

It mounts a Volume under the `/repo` path with the idea of manually cloning the repository and then fetching the necessary models.
First let's deploy the triton server:

```bash
$ oc apply -f deploy/triton-server.yaml
deployment.apps/triton-server created
service/triton-server created
persistentvolumeclaim/morpheus-repo created
```

The first time you deploy the `triton-server` you will need to create a debug pod for the `triton-server` deployment.

```bash
oc debug deployment/triton-server
```

Now you have to install the `git-lfs` command

```bash
# add the repository
curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | bash
# install git-lfs
apt-get install git-lfs
# clone the repository
git clone https://github.com/nv-morpheus/Morpheus.git /repo/Morpheus
# fetch the models
cd /repo/Morpheus
./scripts/fetch_data.py fetch models
```

After exiting the debug pod you might need to delete the triton-server pod that is not able to start due to missing all models.

```bash
oc delete pod -l app=triton-server
```

In the logs you should see that the models are loaded. In my case there were 2 models not loaded.
The reason of these models not loading is [here](https://github.com/nv-morpheus/Morpheus/tree/branch-24.03/models/triton-model-repo/phishing-bert-trt/1#generating-trt-models-from-onnx)

```
+------------------------+---------+-------------------------------------------------------------------------------------------------------------------------------------------------+
| Model                  | Version | Status                                                                                                                                          |
+------------------------+---------+-------------------------------------------------------------------------------------------------------------------------------------------------+
| abp-nvsmi-xgb          | 1       | READY                                                                                                                                           |
| all-MiniLM-L6-v2       | 1       | READY                                                                                                                                           |
| log-parsing-onnx       | 1       | READY                                                                                                                                           |
| phishing-bert-onnx     | 1       | READY                                                                                                                                           |
| phishing-bert-trt      | 1       | UNAVAILABLE: Internal: unable to load plan file to auto complete config: /repo/Morpheus/models/triton-model-repo/phishing-bert-trt/1/model.plan |
| root-cause-binary-onnx | 1       | READY                                                                                                                                           |
| sid-minibert-onnx      | 1       | READY                                                                                                                                           |
| sid-minibert-trt       | 1       | UNAVAILABLE: Internal: unable to load plan file to auto complete config: /repo/Morpheus/models/triton-model-repo/sid-minibert-trt/1/model.plan  |
+------------------------+---------+-------------------------------------------------------------------------------------------------------------------------------------------------+
```

## Custom VDB Upload

```bash
python examples/llm/main.py --log_level=DEBUG vdb_upload pipeline --enable_cache --enable_monitors --embedding_model_name all-MiniLM-L6-v2 --triton_server_url=triton-server:8001 --vector_db_uri=http://milvus-standalone:19530 --feed_inputs https://access.redhat.com/security/data/meta/v1/rhsa.rss --feed_inputs https://developers.redhat.com/blog/feed --feed_inputs https://www.redhat.com/en/rss/blog
```

Using a configuration file

```bash
python examples/llm/main.py vdb_upload pipeline --vdb_config_path examples/llm/vdb_upload/vdb_rh_config.yaml
```

```bash
python examples/llm/main.py --log_level=DEBUG rag pipeline --llm_service=OpenAI --vector_db_uri=http://milvus-standalone:19530 --model_name=gpt-3.5-turbo
```
