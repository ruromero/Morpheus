FROM nvcr.io/nvidia/morpheus/morpheus:v24.03.02-runtime

RUN mamba env update \
  -n morpheus \
  --file ./conda/environments/all_cuda-121_arch-x86_64.yaml && \
  conda update -n morpheus -c conda-forge conda && \
  pip install --yes debugpy

ENTRYPOINT ["sleep", "infinity"]