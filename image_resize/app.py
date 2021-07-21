import boto3
import uuid
import os
from urllib.parse import unquote_plus
from PIL import Image
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

engine = create_engine(os.environ.get('DATABASE_URL'))
Base = declarative_base()

s3_client = boto3.client('s3')

def create_thumbnail_handler(event, context):
  for record in event['Records']:
    bucket = record['s3']['bucket']['name']
    key = unquote_plus(record['s3']['object']['key'])

    create_thumbnail(bucket, key)

    image_url = f'https://s3-eu-central-1.amazonaws.com/{bucket}/{key}'
    resized_image_url = f'https://s3-eu-central-1.amazonaws.com/{bucket}-resized/{key}'
    
    session = create_db_session(engine)
    thumbnail = Thumbnail(image_url=image_url, resized_image_url=resized_image_url)
    session.add()
    session.commit()


def create_thumbnail(bucket, key):
  tmpkey = key.replace('/', '')

  if not image_file(tmpkey):
    return

  download_path = '/tmp/{}{}'.format(uuid.uuid4(), tmpkey)
  upload_path = '/tmp/resized-{}'.format(tmpkey)
  s3_client.download_file(bucket, key, download_path)
  resize_image(download_path, upload_path)
  s3_client.upload_file(upload_path, '{}-resized'.format(bucket), key)

def resize_image(image_path, resized_path):
  with Image.open(image_path) as image:
    image.thumbnail(tuple(x / 2 for x in image.size))
    image.save(resized_path)

def image_file(file_name):
  return file_name.endswith('.jpg') or file_name.endswith('.png')


class Thumbnail(Base):
  __tablename__ = 'Thumbnails'

  id = Column(Integer, primary_key=True)
  image_url = Column(String)
  resized_image_url = Column(String)


def create_db_session(engine):
    global Session
    if not Session:
        Session = sessionmaker(bind=engine)

