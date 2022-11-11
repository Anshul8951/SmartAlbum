import json
import boto3
import requests
import inflect
#from requests_aws4auth import AWS4Auth

def push_to_lex(query):
    #added old comment 1 for checking
    lex = boto3.client('lex-runtime')
    print("lex client initialized")
    response = lex.post_text(
        botName='smartAlbum',                 
        botAlias='smartAlbum',
        userId='root',           
        inputText=query
    )

    print("test changes new")
    print("lex-response", response)
    labels = []
    if 'slots' not in response:
        print("No photo collection for query {}".format(query))
    else:
        print ("slot: ",response['slots'])
        slot_val = response['slots']
        for key,value in slot_val.items():
            if value!=None:
                labels.append(value)
    return labels


def search_elastic_search(labels):
    print("Inside elastic search")
    region = 'us-east-1' 
    service = 'es'
    credentials = boto3.Session().get_credentials()
    #awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
    url = 'https://search-photos-4xczjcwzga47g5txcwnch6vy5i.us-east-1.es.amazonaws.com/photos/_search?q='

    resp = []
    for label in labels:
        if (label is not None) and label != '':
            url2 = url+label
            print(label)
            print(url2)
            resp.append(requests.get(url2, auth=('admin', 'Admin@1234')).json())
    print ("RESPONSE" , resp)
    output = []
    bucket_url = "https://store-photos-b2.s3.amazonaws.com/"
    for r in resp:
        if 'hits' in r:
             for val in r['hits']['hits']:
                key = val['_source']['objectKey']
                if bucket_url+key not in output:
                    output.append(bucket_url+key)
    print(output)
    return output
    

def lambda_handler(event, context):
    # TODO implement
    
    p = inflect.engine()
    
    q = (event['queryStringParameters']['q'])

    labels = push_to_lex(str(q))
    
    
    allLabels = []
    for label in labels:
        print(label)
        if(p.singular_noun(label) == False):
            allLabels.append(label)
            allLabels.append(p.plural(label))
        else:
            allLabels.append(label)
            allLabels.append(p.singular_noun(label))

    print("allLabels", allLabels)
    
    print("labels as is: ", labels)
    labels = allLabels
    print("labels with both singular and plurals: ", labels)
    
    if len(labels) != 0:
        print("len(labels) != 0")
        img_paths = search_elastic_search(labels)
    if not img_paths:
        return{
            'statusCode':404,
            'headers': {"Access-Control-Allow-Origin":"*","Access-Control-Allow-Methods":"*","Access-Control-Allow-Headers": "*"},
            'body': json.dumps('No Results found')
        }
    else:  
        return{
            'statusCode': 200,
            'headers': {"Access-Control-Allow-Origin":"*","Access-Control-Allow-Methods":"*","Access-Control-Allow-Headers": "*"},
            'body': json.dumps(img_paths)
        }
    return