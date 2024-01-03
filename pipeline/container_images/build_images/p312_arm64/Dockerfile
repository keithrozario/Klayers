FROM public.ecr.aws/lambda/python:3.12-arm64

COPY build.py ./
RUN pip install --upgrade pip
RUN pip install boto3
RUN pip install aws-lambda-powertools

# Use dnf instead of yum
# https://aws.amazon.com/blogs/compute/python-3-12-runtime-now-available-in-aws-lambda/
RUN dnf update
RUN dnf install -y python-devel

CMD ["build.main"]