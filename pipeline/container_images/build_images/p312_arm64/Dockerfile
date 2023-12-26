FROM public.ecr.aws/lambda/python:3.12-arm64

COPY build.py ./
RUN pip install --upgrade pip
RUN pip install boto3
RUN pip install aws-lambda-powertools
RUN dnf update
RUN dnf install -y python-devel

CMD ["build.main"]