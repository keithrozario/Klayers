FROM public.ecr.aws/lambda/python:3.10-arm64

COPY requirements.txt ./
COPY build.py ./
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN yum install -y python-devel

CMD ["build.main"]