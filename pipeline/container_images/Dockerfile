ARG BASE_IMAGE_TAG=3.14
FROM public.ecr.aws/lambda/python:${BASE_IMAGE_TAG}

RUN dnf update -y && dnf install -y python-devel && dnf clean all
RUN pip install --no-cache-dir --upgrade pip boto3 aws-lambda-powertools

COPY build.py ${LAMBDA_TASK_ROOT}/
CMD ["build.main"]
