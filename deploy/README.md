# Deploy on OpenShift

# Morpheus

Deploy Morpheus as root. Grant to run as anyuid

```
oc adm policy add-scc-to-user anyuid -z morpheus-sa
```

Deploy morpheus
```
oc apply -f deploy/morpheus.yaml
```

Update the conda environment

```
mamba env update \
  -n ${CONDA_DEFAULT_ENV} \
  --file ./conda/environments/all_cuda-121_arch-x86_64.yaml
```

Run the example:

```
python examples/llm/main.py vdb_upload pipeline --enable_cache --enable_monitors --embedding_model_name all-MiniLM-L6-v2 --triton_server_url=triton-server:8001 --vector_db_uri=http://milvus-standalone:19530
```

## Triton Server

It mounts a Volume under the `/repo` path with the idea of manually cloning the repository and then fetching the necessary models.

The first time you deploy the `triton-server` you will need to create a debug pod for the `triton-server` deployment.

```
oc debug deployment/triton-server
```

Now you have to install the `git-lfs` command

```
# add the repository
curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | bash
# install git-lfs
apt-get install git-lfs
# clone the repository
git clone git@github.com:nv-morpheus/Morpheus.git /repo/Morpheus
# fetch the models
cd /repo/Morpheus
./scripts/fetch_data.py fetch all
```

You can now exit the debug pod and in the logs you should see that the models are loaded. In my case there were 2 models not loaded.

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