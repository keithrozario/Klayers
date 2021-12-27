FROM public.ecr.aws/lambda/python:3.9
 
COPY app.py ./
COPY requirements.txt ./
RUN yum install -y python-devel 
RUN pip install -r requirements.txt
 
# You can overwrite command in `serverless.yml` template
CMD ["app.handler"]