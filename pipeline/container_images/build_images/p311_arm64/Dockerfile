FROM public.ecr.aws/lambda/python:3.11-arm64

COPY build.py ./
RUN pip install --upgrade pip
RUN pip install boto3
RUN pip install aws-lambda-powertools
RUN yum install -y python-devel

CMD ["build.main"]