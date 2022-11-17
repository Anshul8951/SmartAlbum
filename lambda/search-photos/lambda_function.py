import json
import boto3
import requests
import inflect

def push_to_lex(query):
    #added old comment 1 for checking pipeline
    lex = boto3.client('lexv2-runtime')
    print("lex client initialized")
    response = lex.recognize_text(
        botId = 'ILOO46TTNY',
        botAliasId = 'TND07SJU8W',
        localeId = 'en_US',
        sessionId = "root",
        text = query
    )

    print("lex-response", response)
    
    val1 = response['sessionState']['intent']['slots']['querya']
    val2 = response['sessionState']['intent']['slots']['queryb']
    labels = []
    
    if(val1 != None):
        labels.append(val1['value']['interpretedValue'])
    if(val2 != None):
        labels.append(val2['value']['interpretedValue'])
    
    if len(labels) == 0:
        print("No photo collection for query {}".format(query))
    
    return labels


def search_elastic_search(labels):
    print("Inside elastic search")
    region = 'us-east-1' 
    service = 'es'
    credentials = boto3.Session().get_credentials()
    #awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
    url = 'https://search-photos-ouj7lbnotviwpf46xyx4nfzcni.us-east-1.es.amazonaws.com/photos/_search?q='
    

    resp = []
    for label in labels:
        if (label is not None) and label != '':
            url2 = url+label
            print(label)
            print(url2)
            resp.append(requests.get(url2, auth=('master_user', 'Suits1998*')).json())
    print ("RESPONSE" , resp)
    output = []
    bucket_url = "https://photosalbumb21.s3.amazonaws.com/"
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