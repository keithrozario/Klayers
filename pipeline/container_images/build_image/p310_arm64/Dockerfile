FROM public.ecr.aws/lambda/python:3.10-arm64

COPY requirements.txt ./
RUN pip install -r requirements.txt
RUN yum install -y python-devel
COPY build.py ./

CMD ["build.main"]