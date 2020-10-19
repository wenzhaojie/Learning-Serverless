# -*- coding: utf-8 -*-

from PIL import Image, ImageFont, ImageDraw
from qcloud_cos_v5 import CosConfig
from qcloud_cos_v5 import CosS3Client
from qcloud_cos_v5 import CosServiceError
from qcloud_cos_v5 import CosClientError

appid = u'130xxxx901'  # 请替换为您的 APPID
secret_id = u'AKIDRgxxxxxxxxxxxxxrBgZP4'  # 请替换为您的 SecretId
secret_key = u'b9RikaxxxxxxxxxxxxxxxxRpFEzV'  # 请替换为您的 SecretKey
token = None
region = u'ap-guangzhou'  # 请替换为您bucket 所在的地域
font_bucket = u'env-130xxxx901' # 请替换为存放字体文件的bucket
to_bucket = u'results-130xxxx901'  # 请替换为您用于存放压缩后图片的bucket，字体文件为font.ttf

config = CosConfig(Secret_id=secret_id, Secret_key=secret_key, Region=region, Token=token)
client = CosS3Client(config)

response = client.get_object(Bucket=font_bucket, Key="font.ttf", ) # 从存储桶下载字体文件
response['Body'].get_stream_to_file('/tmp/font.ttf')

def add_word(pic_path, save_path):
    # 打开图片
    im = Image.open(pic_path).convert('RGBA')
    # 新建一个空白图片,尺寸与打开图片一样
    txt = Image.new('RGBA', im.size, (0, 0, 0, 0))
    # 设置字体
    fnt = ImageFont.truetype("/tmp/font.ttf", 40)
    # 操作新建的空白图片>>将新建的图片添入画板
    d = ImageDraw.Draw(txt)
    # 在新建的图片上添加字体
    d.text((txt.size[0] - 220, txt.size[1] - 80), "此处为您所添加的文字水印", font=fnt,  fill=(255, 255, 255, 255))
    # 合并两个图片
    out = Image.alpha_composite(im, txt)
    # 保存图像
    out.save(save_path)

def handler(event, context):
    for record in event['Records']:
        try:
            bucket = record['cos']['cosBucket']['name'] + '-' + str(appid)
            key = record['cos']['cosObject']['key']
            key = key.replace('/' + str(appid) + '/' + record['cos']['cosBucket']['name'] + '/', '', 1)
            download_path = '/tmp/{}'.format(key)
            upload_path = '/tmp/new_pic-{}'.format(key)
            
            # 下载图片
            try:
                response = client.get_object(Bucket=bucket, Key=key, )
                response['Body'].get_stream_to_file(download_path)
            except CosServiceError as e:
                
                print(e.get_error_code())
                print(e.get_error_msg())
                print(e.get_resource_location())

            # 图像增加水印
            add_word(download_path, upload_path)


            # 图像上传
            response = client.put_object_from_local_file(
                Bucket=to_bucket,
                LocalFilePath=upload_path,
                Key=("upload-" + key)
            )

        except Exception as e:
            print(e)
