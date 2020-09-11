
import boto3
import json
import logging
import os
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import CloudFlare

load_dotenv()

bucket_name = os.getenv("BUCKET_NAME")
bucket_region = os.getenv("BUCKET_REGION")
cloudflare_token = os.getenv("CLOUDFLARE_TOKEN")
zone_id = os.getenv("ZONE_ID")
record_name = os.getenv("RECORD_NAME")


def create_bucket(bucket_name, region):
    """Create an S3 bucket in a specified region

    If a region is not specified, the bucket is created in the S3 default
    region (us-east-1).

    :param bucket_name: Bucket to create
    :param region: String region to create bucket in, e.g., 'us-west-2'
    :return: True if bucket created, else False
    """

    # Create bucket
    try:
        if region == 'us-east-1':
            s3_client = boto3.client('s3')
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            s3_client = boto3.client('s3', region_name=region)
            location = {'LocationConstraint': region}
            s3_client.create_bucket(Bucket=bucket_name,
                                    CreateBucketConfiguration=location)
    except ClientError as e:
        logging.error(e)
        return False
    return True

def put_website(bucket_name):


    s3 = boto3.client('s3')

    bucket_policy = {
        'Version': '2012-10-17',
        'Statement': [{
            'Sid': 'AddPerm',
            'Effect': 'Allow',
            'Principal': '*',
            'Action': ['s3:GetObject'],
            'Resource': "arn:aws:s3:::%s/*" % bucket_name
         }]
    }
    bucket_policy = json.dumps(bucket_policy)
    s3.put_bucket_policy(Bucket=bucket_name, Policy=bucket_policy)

    s3.put_bucket_website(
        Bucket=bucket_name,
        WebsiteConfiguration={
        'ErrorDocument': {'Key': 'index.html'},
        'IndexDocument': {'Suffix': 'index.html'},
        }
    )

def get_endpoint(bucket_name, bucket_region):
    return ''.join((bucket_name, '.s3-website.', bucket_region, '.amazonaws.com'))


def put_dns_record(website_endpoint, cloudflare_token, zone_id, record_name):
    cf = CloudFlare.CloudFlare(token=cloudflare_token)
    cf.zones.dns_records.post(zone_id, data = {
        'name': record_name,
        'type': 'CNAME',
        'content': website_endpoint,
        'proxied': True
    }
    )

create_bucket(bucket_name, bucket_region)
put_website(bucket_name)
website_endpoint = get_endpoint(bucket_name, bucket_region)
put_dns_record(website_endpoint, cloudflare_token, zone_id, record_name)


