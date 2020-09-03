import boto3, json, time, datetime, sys, os


def get_key_expiry_days(username ):
    client = boto3.client('iam')
    res = client.list_access_keys(UserName=username)
    key_1_age = 0 
    key_2_age = 0 

    if (len(res['AccessKeyMetadata'])>=1):
        key_1_age = compute_age(res['AccessKeyMetadata'][0])
    if (len(res['AccessKeyMetadata'])==2):
        key_2_age = compute_age(res['AccessKeyMetadata'][1])

    # return which ever is bigger
    if (key_1_age > key_2_age):
        return(key_1_age)
    else:
        return(key_2_age)

def compute_age(res):
    if (res['Status'] != 'Active'):
        return(0)

    accesskeydate = res['CreateDate'] ### Use for loop if you are going to run this on production. I just wrote it real quick
    accesskeydate = accesskeydate.strftime("%Y-%m-%d %H:%M:%S")
    currentdate = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    accesskeyd = time.mktime(datetime.datetime.strptime(accesskeydate, "%Y-%m-%d %H:%M:%S").timetuple())
    currentd = time.mktime(datetime.datetime.strptime(currentdate, "%Y-%m-%d %H:%M:%S").timetuple())
    active_days = (currentd - accesskeyd)/60/60/24 ### We get the data in seconds. converting it to days
    return (int(round(active_days)))


def main(event, context):
    key_age_threshold = os.enviorn("key_age_threshold") #45
    notify_dl = os.enviorn("notify_dl") #"vijay.mishra@ihsmarkit.com"
    
    client = boto3.client('iam') 
    response = client.list_users()
    notify=[]
    msg_body = "Credentials for following IAM users are set to expire soon. Please rotate your keys ASAP to avoid access keys getting disabled.\n"

    for user in response['Users']:
        iam_user = user['UserName']
        age = get_key_expiry_days(iam_user)
        if (age >= key_age_threshold):
            msg_body = msg_body + "\n" + iam_user + "["+  str(age) + " days old]"  
            notify.append (dict(zip(("iam_user", "key_age") ,  (iam_user, age)))) 


    client = boto3.client('ses')
    response = client.send_email(
        Destination={
            'ToAddresses': [notify_dl],
        },
        Message={
            'Body': {
                'Text': {
                    'Charset': 'UTF-8',
                    'Data': msg_body,
                },
            },
            'Subject': {
                'Charset': 'UTF-8',
                'Data': 'IAM User Access Keys EXPIRY Notification',
            },
        },
        Source='vijay.mishra@ihsmarkit.com',
    )
    print(response)
