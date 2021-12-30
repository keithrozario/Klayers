FROM public.ecr.aws/lambda/python:3.9
 
COPY build.py ./
COPY requirements.txt ./
RUN yum install -y python-devel 
RUN pip install -r requirements.txt

CMD ["build.main"]